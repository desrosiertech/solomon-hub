#!/usr/bin/env python3
"""Phase 0 Ollama benchmark. Local-only. No household data leaves the machine.

Usage:
  python3 bench/run_benchmark.py --model qwen3:8b --out bench/results.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def chat(host: str, model: str, messages: list, tools: list, timeout: int = 180) -> dict:
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "temperature": 0,
        }
    ).encode()
    req = urllib.request.Request(
        host.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        return {"error": str(exc), "latency_s": time.perf_counter() - t0}
    payload["latency_s"] = time.perf_counter() - t0
    return payload


def tool_names(completion: dict) -> list[str]:
    try:
        calls = completion["choices"][0]["message"].get("tool_calls") or []
    except (KeyError, IndexError, TypeError):
        return []
    names = []
    for call in calls:
        fn = call.get("function") or {}
        if fn.get("name"):
            names.append(fn["name"])
    return names


def first_args(completion: dict) -> dict:
    try:
        raw = completion["choices"][0]["message"]["tool_calls"][0]["function"].get("arguments") or "{}"
        return json.loads(raw) if isinstance(raw, str) else raw
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return {}


def score_task(task: dict, completion: dict) -> dict:
    names = tool_names(completion)
    args = first_args(completion)
    expect = task.get("expect_tool")
    forbid = task.get("forbid_tools") or []
    contain = task.get("expect_args_contain") or {}
    ok_expect = (expect is None) or (expect in names)
    ok_forbid = not any(n in names for n in forbid)
    ok_args = all(args.get(k) == v or (isinstance(args.get(k), str) and str(v).lower() in str(args.get(k)).lower()) for k, v in contain.items())
    # quantity/count: allow int 2 vs 2
    if not ok_args:
        ok_args = all(str(args.get(k)) == str(v) for k, v in contain.items())
    passed = ok_expect and ok_forbid and (ok_args if contain else True)
    if expect is None and not forbid:
        passed = "error" not in completion
    return {
        "id": task["id"],
        "passed": bool(passed),
        "tools_called": names,
        "args": args,
        "latency_s": completion.get("latency_s"),
        "error": completion.get("error"),
    }


def pad_tokens(approx: int) -> str:
    # ~1 token ≈ 4 chars for English JSON-ish padding.
    unit = '{"dow":"Fri","title":"Practice","who":"Kid1"}'
    n = max(1, (approx * 4) // len(unit))
    return "[" + ",".join(unit for _ in range(n)) + "]"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default=str(Path(__file__).with_name("household-tasks.json")))
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip-long-context", action="store_true")
    args = parser.parse_args()

    spec = json.loads(Path(args.tasks).read_text())
    results = {
        "model": args.model,
        "host": args.host,
        "measured": False,
        "note": "Fill hardware fields by hand (nvidia-smi, ollama ps, Plex state).",
        "hardware": {
            "hostname": None,
            "gpu": None,
            "vram_mb": None,
            "plex_transcode_during_run": None,
        },
        "tasks": [],
        "long_context": [],
    }

    system = spec["system"]
    tools = spec["tools"]
    for task in spec["tasks"]:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": task["prompt"]},
        ]
        completion = chat(args.host, args.model, messages, tools)
        results["tasks"].append(score_task(task, completion))

    if not args.skip_long_context:
        for n in spec["long_context"]["target_tokens"]:
            prompt = (
                "Here is cached household JSON. Write a two-sentence briefing. "
                "Do not call tools.\n" + pad_tokens(n)
            )
            completion = chat(
                args.host,
                args.model,
                [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                tools=[],
                timeout=300,
            )
            usage = completion.get("usage") or {}
            results["long_context"].append(
                {
                    "target_tokens": n,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "latency_s": completion.get("latency_s"),
                    "error": completion.get("error"),
                }
            )

    passed = sum(1 for t in results["tasks"] if t["passed"])
    results["task_score"] = f"{passed}/{len(results['tasks'])}"
    results["measured"] = True
    Path(args.out).write_text(json.dumps(results, indent=2))
    print(json.dumps({"out": args.out, "task_score": results["task_score"]}, indent=2))


if __name__ == "__main__":
    main()
