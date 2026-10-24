import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type CalendarEntry, type DayCard, type HomePayload } from "../api";
import { IdeasList } from "../ui/IdeasList";
import { UseSoonList } from "../ui/UseSoonList";

export function HomePage() {
  const home = useQuery({ queryKey: ["home"], queryFn: api.home });

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_17rem]">
      <div className="grid gap-6">
        <p className="text-2xl">{home.data?.date_label ?? "Today"}</p>
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
      <WeatherCard home={home.data} pending={home.isPending} />
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
      {calendar?.state === "empty" && (
        <p className="mb-4 text-muted">
          Nothing on the calendar yet. Add an event and it will show up here.
        </p>
      )}
      {home && calendar?.state !== "unknown" && calendar?.state !== "empty" && (
        <UpNext rows={home.up_next} />
      )}
      {home && calendar?.state !== "unknown" && <DayCards cards={home.day_cards} />}
      {home && <AddEventForm cards={home.day_cards} />}
    </section>
  );
}

function UpNext({ rows }: { rows: CalendarEntry[] }) {
  if (rows.length === 0) {
    return <p className="text-muted">Nothing else coming up.</p>;
  }
  return (
    <ul className="divide-y divide-line">
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

function DayCards({ cards }: { cards: DayCard[] }) {
  return (
    <ul className="mt-4 grid gap-3 sm:grid-cols-2">
      {cards.map((card) => (
        <li key={card.member_id ?? "everyone"} className="rounded-xl border border-line p-3">
          <p className="mb-2 text-sm text-muted">
            <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full border border-line text-xs text-ink">
              {card.initial}
            </span>
            {card.display_name}
          </p>
          {card.events.length === 0 ? (
            <p className="text-ink">—</p>
          ) : (
            <ul>
              {card.events.map((event) => (
                <li key={event.id}>
                  {event.when_label} {event.title}
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}

function AddEventForm({ cards }: { cards: DayCard[] }) {
  const queryClient = useQueryClient();
  const members = cards.filter((card) => card.member_id);
  const [title, setTitle] = useState("");
  const [startLocal, setStartLocal] = useState("");
  const [location, setLocation] = useState("");
  const [memberId, setMemberId] = useState(members[0]?.member_id ?? "");
  const [error, setError] = useState<string | null>(null);
  const add = useMutation({
    mutationFn: api.addEvent,
    onSuccess: async () => {
      setTitle("");
      setLocation("");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["home"] });
    },
    onError: () => setError("That event could not be saved."),
  });

  return (
    <form
      className="mt-5 grid gap-3 border-t border-line pt-4"
      onSubmit={(event) => {
        event.preventDefault();
        add.mutate({
          title,
          start_local: startLocal,
          location,
          member_id: memberId || null,
        });
      }}
    >
      <h3 className="text-lg">Add an event</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-sm text-muted">
          Title
          <input
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="rounded-xl border border-line bg-canvas px-3 py-2 text-base text-ink"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          When (New York)
          <input
            required
            type="datetime-local"
            value={startLocal}
            onChange={(event) => setStartLocal(event.target.value)}
            className="rounded-xl border border-line bg-canvas px-3 py-2 text-base text-ink"
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Who
          <select
            value={memberId}
            onChange={(event) => setMemberId(event.target.value)}
            className="rounded-xl border border-line bg-canvas px-3 py-2 text-base text-ink"
          >
            {members.map((card) => (
              <option key={card.member_id} value={card.member_id ?? ""}>
                {card.display_name}
              </option>
            ))}
            <option value="">Everyone</option>
          </select>
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Where
          <input
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            className="rounded-xl border border-line bg-canvas px-3 py-2 text-base text-ink"
          />
        </label>
      </div>
      {error && <p className="text-sm text-muted">{error}</p>}
      <button
        type="submit"
        disabled={add.isPending}
        className="w-fit rounded-full bg-accent px-4 py-2 text-on-accent disabled:opacity-50"
      >
        Add event
      </button>
    </form>
  );
}

function WeatherCard({ home, pending }: { home?: HomePayload; pending: boolean }) {
  const weather = home?.weather;
  return (
    <aside className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl">Weather</h2>
        {weather?.chip && <Chip text={weather.chip} />}
      </div>
      {pending && (
        <div className="h-24 animate-pulse rounded-xl bg-wash" aria-busy="true" aria-label="Loading weather" />
      )}
      {weather?.state === "empty" && <p className="text-muted">Weather has not come in yet.</p>}
      {weather?.state === "unknown" && (
        <p className="text-muted">Weather has not come in. This is not a forecast.</p>
      )}
      {weather && (weather.state === "ready" || weather.state === "stale") && (
        <div>
          <p className="text-4xl tabular-nums">{weather.temp_f}°</p>
          <p className="mt-1 text-muted tabular-nums">
            H {weather.high_f} L {weather.low_f}
          </p>
          <p className="mt-2">{weather.summary}</p>
        </div>
      )}
    </aside>
  );
}
