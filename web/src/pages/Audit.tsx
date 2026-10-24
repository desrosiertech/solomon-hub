import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

const ACTION_COPY: Record<string, string> = {
  "inventory.added": "Added inventory item",
  "suggestion.stop_asking": "Stop asking",
  "inventory.presumed_discarded": "Presumed discarded",
};

export function AuditPage() {
  const audit = useQuery({ queryKey: ["audit"], queryFn: api.audit });

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-sm">
      <h2 className="mb-3 text-2xl">History</h2>
      {audit.isPending && <p className="text-muted">Loading history…</p>}
      <ol className="space-y-3">
        {audit.data?.events.map((event) => (
          <li key={event.id} className="rounded-xl bg-canvas px-4 py-3">
            <p className="text-lg">{ACTION_COPY[event.action] ?? event.action}</p>
            <p className="text-sm text-muted">
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
