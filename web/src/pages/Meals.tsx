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
      <p
        role="status"
        className="w-fit rounded-full bg-wash px-3 py-1 text-sm text-ink tabular-nums"
      >
        {meals.data?.reader.label ?? "Reader …"}
      </p>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-2xl">Ideas from what we have</h2>
          {card?.state === "stale" && (
            <p className="rounded-full bg-wash px-3 py-1 text-sm text-ink">
              {staleLabel(card.generated_at, card.now)}
            </p>
          )}
        </div>
        {meals.isPending && (
          <div className="space-y-3" aria-busy="true" aria-label="Loading dinner ideas">
            <div className="h-16 animate-pulse rounded-xl bg-wash" />
            <div className="h-16 animate-pulse rounded-xl bg-wash" />
          </div>
        )}
        {card?.state === "empty" && <p className="text-muted">Nothing to cook from yet.</p>}
        {meals.data && card?.state !== "empty" && <IdeasList ideas={meals.data.ideas} />}
      </section>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-1 text-2xl">Use soon</h2>
        <p className="mb-3 text-sm text-muted">
          Quiet freshness notes. These are estimated use-by windows, not alerts.
        </p>
        {meals.isPending && <p className="text-muted">Checking estimated use-by windows…</p>}
        {meals.data && <UseSoonList rows={meals.data.use_soon} />}
      </section>
      <PlannedAndBank />
    </div>
  );
}

function PlannedAndBank() {
  const nights = useQuery({ queryKey: ["planned"], queryFn: api.plannedMeals });
  const recipes = useQuery({ queryKey: ["recipes"], queryFn: api.recipes });

  return (
    <>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-3 text-2xl">Planned</h2>
        {nights.isPending && <p className="text-muted">Loading the plan…</p>}
        {nights.data && nights.data.nights.length === 0 && (
          <p className="text-muted">No dinners planned yet.</p>
        )}
        <ul className="divide-y divide-line">
          {nights.data?.nights.map((night) => (
            <li key={night.on} className="py-3 first:pt-0 last:pb-0">
              <p className="text-lg">{night.title}</p>
              <p className="text-sm text-muted">{night.on}</p>
            </li>
          ))}
        </ul>
      </section>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-3 text-2xl">Recipe bank</h2>
        {recipes.isPending && <p className="text-muted">Loading recipes…</p>}
        {recipes.data && recipes.data.recipes.length === 0 && (
          <p className="text-muted">No recipes banked yet.</p>
        )}
        <ul className="divide-y divide-line">
          {recipes.data?.recipes.map((recipe) => (
            <li key={recipe.id} className="py-3 first:pt-0 last:pb-0">
              <p className="text-lg">{recipe.title}</p>
              {recipe.ingredients.length > 0 && (
                <p className="text-sm text-muted">
                  {recipe.ingredients.map((item) => item.replaceAll("_", " ")).join(", ")}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
