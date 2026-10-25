import { useQuery } from "@tanstack/react-query";
import { api, type CalendarEntry, type HomePayload } from "../api";
import { DayCards } from "../ui/DayCards";
import { IdeasList } from "../ui/IdeasList";
import { UseSoonList } from "../ui/UseSoonList";

export function HomePage() {
  const home = useQuery({ queryKey: ["home"], queryFn: api.home });

  return (
    <div className="grid gap-6">
      <p className="text-3xl font-semibold tracking-tight">{home.data?.date_label ?? "Today"}</p>
      <CalendarSection home={home.data} pending={home.isPending} />
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
    </div>
  );
}

function Chip({ text }: { text: string }) {
  return <p className="rounded-full bg-wash px-3 py-1 text-sm text-ink">{text}</p>;
}

function CalendarSection({ home, pending }: { home?: HomePayload; pending: boolean }) {
  const calendar = home?.calendar;

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl">Up next</h2>
        {calendar?.chip && <Chip text={calendar.chip} />}
      </div>
      {pending && (
        <div className="space-y-3" aria-busy="true" aria-label="Loading the calendar">
          <div className="h-14 animate-pulse rounded-xl bg-wash" />
          <div className="h-14 animate-pulse rounded-xl bg-wash" />
        </div>
      )}
      {calendar?.state === "unknown" && (
        <p className="text-muted">Calendar has not come in. This is not an empty day.</p>
      )}
      {calendar?.state === "empty" && <p className="mb-4 text-muted">Nothing on the calendar yet.</p>}
      {home && calendar?.state !== "unknown" && calendar?.state !== "empty" && <UpNext rows={home.up_next} />}
      {home && calendar?.state !== "unknown" && <DayCards cards={home.day_cards} />}
    </section>
  );
}

function UpNext({ rows }: { rows: CalendarEntry[] }) {
  if (rows.length === 0) {
    return <p className="mb-4 text-muted">Nothing else coming up.</p>;
  }
  return (
    <ul className="mb-4 divide-y divide-line">
      {rows.map((row) => (
        <li key={row.id} className="flex items-start justify-between gap-3 py-3 first:pt-0">
          <div>
            <p className="text-lg">
              <span className="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-line text-sm">
                {row.initial}
              </span>
              {row.when_label} {row.title}
            </p>
            <p className="text-sm text-muted">
              {row.who}
              {row.location ? ` · ${row.location}` : ""}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
