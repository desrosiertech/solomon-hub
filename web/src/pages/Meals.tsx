import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { IdeasList } from "../ui/IdeasList";
import { UseSoonList } from "../ui/UseSoonList";

function staleLabel(generatedAt: string | null, nowIso: string | null): string {
  if (!generatedAt) {
    return "Updated earlier";
  }
  const generated = new Date(generatedAt);
  const now = nowIso ? new Date(nowIso).getTime() : Date.now();
  const minutes = Math.max(0, Math.round((now - generated.getTime()) / 60000));
  if (minutes < 60) {
    return `Updated ${minutes} min ago`;
  }
  const hours = Math.round(minutes / 60);
  return `Updated ${hours} h ago`;
}

export function MealsPage() {
  const meals = useQuery({ queryKey: ["meals"], queryFn: api.meals });
  const card = meals.data?.ideas_card;

  return (
    <div className="grid gap-6">
      <section className="rounded-2xl border border-line bg-card p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-2xl">Ideas from what we have</h2>
          {card?.state === "stale" && (
            <p className="rounded-full bg-sand-soft px-3 py-1 text-sm text-ink">
              {staleLabel(card.generated_at, card.now)}
            </p>
          )}
        </div>
        {meals.isPending && (
          <div className="space-y-3" aria-busy="true" aria-label="Loading dinner ideas">
            <div className="h-16 animate-pulse rounded-xl bg-sand-soft" />
            <div className="h-16 animate-pulse rounded-xl bg-sand-soft" />
          </div>
        )}
        {card?.state === "empty" && (
          <p className="text-muted">
            Nothing to cook from yet. Add a few groceries — a leafy green and a leftover
            are enough to start dinner ideas.
          </p>
        )}
        {meals.data && card?.state !== "empty" && <IdeasList ideas={meals.data.ideas} />}
      </section>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-sm">
        <h2 className="mb-1 text-2xl">Use soon</h2>
        <p className="mb-3 text-sm text-muted">
          Quiet freshness notes. These are estimated use-by windows, not alerts.
        </p>
        {meals.isPending && <p className="text-muted">Checking estimated use-by windows…</p>}
        {meals.data && <UseSoonList rows={meals.data.use_soon} />}
      </section>
    </div>
  );
}
