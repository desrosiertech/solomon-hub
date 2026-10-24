import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "../api";

const CATEGORIES = [
  ["leafy_greens", "Leafy greens"],
  ["cooked_leftovers", "Cooked leftovers"],
  ["berries", "Berries"],
  ["whole_melon", "Whole melon"],
  ["unknown", "Unknown"],
];

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
  const queryClient = useQueryClient();
  const items = useQuery({ queryKey: ["inventory"], queryFn: api.inventory });
  const add = useMutation({
    mutationFn: api.addItem,
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  const [label, setLabel] = useState("");
  const [category, setCategory] = useState("leafy_greens");
  const [storage, setStorage] = useState("fridge");
  const [leftover, setLeftover] = useState(false);
  const [acquiredAt, setAcquiredAt] = useState("");
  const [grace, setGrace] = useState(10);
  const [clock, setClock] = useState("");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    add.mutate({
      label,
      category: leftover ? "cooked_leftovers" : category,
      storage,
      leftover,
      quantity_kind: leftover ? "count" : "one_package",
      quantity_count: leftover ? 2 : undefined,
      acquired_at: acquiredAt ? new Date(acquiredAt).toISOString() : undefined,
    });
    setLabel("");
  }

  const age = useMutation({
    mutationFn: async () => {
      if (clock) {
        await api.setClock(new Date(clock).toISOString());
      }
      await api.settings({
        grace_period_minutes: grace,
        presume_after_minutes: grace,
      });
      return api.age();
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Add groceries</h2>
        <label className="block text-sm text-muted">
          Name
          <input
            required
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          />
        </label>
        <label className="block text-sm text-muted">
          Category
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          >
            {CATEGORIES.map(([value, name]) => (
              <option key={value} value={value}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm text-muted">
          Storage
          <select
            value={storage}
            onChange={(event) => setStorage(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          >
            <option value="fridge">Fridge</option>
            <option value="pantry">Pantry</option>
            <option value="freezer">Freezer</option>
            <option value="counter">Counter</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={leftover}
            onChange={(event) => setLeftover(event.target.checked)}
          />
          Leftover
        </label>
        <label className="block text-sm text-muted">
          Acquired (optional)
          <input
            type="datetime-local"
            value={acquiredAt}
            onChange={(event) => setAcquiredAt(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          />
        </label>
        <button
          type="submit"
          className="rounded-full bg-accent px-4 py-2 text-on-accent disabled:opacity-50"
          disabled={add.isPending}
        >
          Add item
        </button>
        <div className="border-t border-line pt-3">
          <p className="mb-2 text-sm text-muted">
            Slice tools — shorten the grace period and move household time to watch
            stale then presumed discarded.
          </p>
          <label className="block text-sm text-muted">
            Grace and presume-after (minutes)
            <input
              type="number"
              min={1}
              value={grace}
              onChange={(event) => setGrace(Number(event.target.value))}
              className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
            />
          </label>
          <label className="mt-2 block text-sm text-muted">
            Household time
            <input
              type="datetime-local"
              value={clock}
              onChange={(event) => setClock(event.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
            />
          </label>
          <button
            type="button"
            className="mt-3 rounded-full border border-line px-4 py-2"
            onClick={() => age.mutate()}
          >
            Apply time and age inventory
          </button>
        </div>
      </form>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-3 text-2xl">On hand</h2>
        {items.isPending && <p className="text-muted">Loading inventory…</p>}
        <ul className="divide-y divide-line">
          {items.data?.items.map((item) => (
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
    </div>
  );
}
