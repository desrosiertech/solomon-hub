import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { personColor } from "./person";

function nyDate(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(iso));
}

function formatTime(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function RightRail() {
  const home = useQuery({ queryKey: ["home"], queryFn: api.home });
  const nights = useQuery({ queryKey: ["planned"], queryFn: api.plannedMeals });
  const now = home.data?.now;
  const today = now ? nyDate(now) : null;
  const dinner = nights.data?.nights.find((night) => night.on === today);
  const weather = home.data?.weather;
  const next = home.data?.up_next ?? [];
  const colors = new Map<string, string>();
  let memberIndex = 0;
  for (const card of home.data?.day_cards ?? []) {
    const key = card.member_id ?? "";
    if (colors.has(key)) {
      continue;
    }
    colors.set(key, personColor(card.member_id, memberIndex));
    if (card.member_id) {
      memberIndex += 1;
    }
  }

  return (
    <aside className="grid content-start gap-3 lg:sticky lg:top-4" aria-label="Today">
      <section className="rounded-2xl border border-line bg-card px-4 py-4 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <p className="text-5xl font-semibold tracking-tight tabular-nums">{now ? formatTime(now) : "…"}</p>
        <p className="mt-1 text-muted">{home.data?.date_label ?? "Today"}</p>
      </section>

      <section className="rounded-2xl border border-line bg-card px-4 py-4 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-sm font-medium text-muted">Weather</h2>
        {home.isPending && <div className="mt-3 h-16 animate-pulse rounded-xl bg-wash" aria-busy="true" />}
        {weather?.state === "empty" && <p className="mt-2">No weather yet.</p>}
        {weather?.state === "unknown" && (
          <p className="mt-2">Weather has not come in. This is not a forecast.</p>
        )}
        {weather && (weather.state === "ready" || weather.state === "stale") && (
          <div className="mt-1">
            <p className="text-4xl font-semibold tabular-nums">{weather.temp_f}°</p>
            <p className="text-sm text-muted tabular-nums">
              H {weather.high_f}° L {weather.low_f}°
            </p>
            <p className="mt-1">{weather.summary}</p>
            {weather.chip && <p className="mt-2 text-sm text-muted">{weather.chip}</p>}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-card px-4 py-4 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-sm font-medium text-muted">Dinner</h2>
        <p className="mt-1 text-lg">{dinner ? dinner.title : "Nothing planned yet"}</p>
      </section>

      <section className="rounded-2xl border border-line bg-card px-4 py-4 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-sm font-medium text-muted">Next up</h2>
        {home.isPending && <div className="mt-3 h-12 animate-pulse rounded-xl bg-wash" aria-busy="true" />}
        {home.data && next.length === 0 && <p className="mt-2 text-muted">Nothing else coming up.</p>}
        {next.length > 0 && (
          <ul className="mt-2 divide-y divide-line">
            {next.slice(0, 4).map((row) => (
              <li key={row.id} className="flex items-start gap-2 py-2 first:pt-0 last:pb-0">
                <span
                  className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-semibold text-white"
                  style={{ backgroundColor: colors.get(row.member_id ?? "") ?? "#6f6256" }}
                >
                  {row.initial}
                </span>
                <span>
                  <span className="block text-sm">{row.title}</span>
                  <span className="block text-xs text-muted">{row.when_label}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </aside>
  );
}
