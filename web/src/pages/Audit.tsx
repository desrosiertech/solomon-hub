import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

const ACTION_COPY: Record<string, string> = {
  "inventory.added": "Added inventory item",
  "suggestion.stop_asking": "Stop asking",
  "inventory.presumed_discarded": "Presumed discarded",
  "receipt.applied": "Added receipt lines to inventory",
  "recipe.banked": "Banked a recipe",
};

export function AuditPage() {
  const audit = useQuery({ queryKey: ["audit"], queryFn: api.audit });

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <h2 className="mb-3 text-2xl font-semibold tracking-tight">History</h2>
      {audit.isPending && <p className="text-muted">Loading history…</p>}
      <ol className="divide-y divide-line">
        {audit.data?.events.map((event) => (
          <li key={event.id} className="py-3 first:pt-0 last:pb-0">
            <p className="text-lg">{ACTION_COPY[event.action] ?? event.action}</p>
            <p className="text-sm text-muted tabular-nums">
              {event.actor_kind === "job" ? "Aging job" : "Adult"} ·{" "}
              {new Date(event.at).toLocaleString()}
            </p>
            {event.detail && <p className="text-sm">{event.detail}</p>}
          </li>
        ))}
      </ol>
    </section>
  );
}
