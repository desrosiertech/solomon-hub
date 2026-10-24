import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { IdeasList } from "../ui/IdeasList";
import { UseSoonList } from "../ui/UseSoonList";

export function HomePage() {
  const home = useQuery({ queryKey: ["home"], queryFn: api.home });

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-3 text-2xl">Ideas from what we have</h2>
        {home.isPending && <p className="text-muted">Looking through the fridge…</p>}
        {home.data && <IdeasList ideas={home.data.ideas} />}
      </section>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="mb-3 text-2xl">Use soon</h2>
        {home.isPending && <p className="text-muted">Checking estimated use-by windows…</p>}
        {home.data && <UseSoonList rows={home.data.use_soon} />}
      </section>
    </div>
  );
}
