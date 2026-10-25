import { useQuery } from "@tanstack/react-query";
import { api } from "../api";

function stateCopy(state: string): string {
  if (state === "presumed_discarded") {
    return "Presumed discarded";
  }
  if (state === "past_window") {
    return "May be past its expected freshness window";
  }
  if (state === "use_soon") {
    return "Use soon";
  }
  if (state === "stale") {
    return "Stale";
  }
  return "Active";
}

export function InventoryPage() {
  const items = useQuery({ queryKey: ["inventory"], queryFn: api.inventory });
  const rows = items.data?.items ?? [];

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <h2 className="mb-3 text-2xl">On hand</h2>
      {items.isPending && <p className="text-muted">Loading inventory…</p>}
      {items.data && rows.length === 0 && (
        <p className="text-muted">Nothing on hand. A receipt or a correction goes through Chat.</p>
      )}
      <ul className="divide-y divide-line">
        {rows.map((item) => (
          <li key={item.id} className="py-3 first:pt-0 last:pb-0">
            <p className="text-lg">
              {item.label}
              {item.leftover ? " · leftover" : ""}
            </p>
            <p className="text-sm text-muted">{item.window_label}</p>
            <p>{item.window_explain}</p>
            <p className="text-sm text-muted">{stateCopy(item.state)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
