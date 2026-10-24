import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type CalendarDay, type DayCard } from "../api";

export function CalendarPage() {
  const [on, setOn] = useState<string | null>(null);
  const day = useQuery({
    queryKey: ["calendar-day", on],
    queryFn: () => api.calendarDay(on),
  });
  const data = day.data;

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-line px-3 py-1 text-ink"
            onClick={() => data && setOn(data.prev)}
            disabled={!data}
          >
            Previous
          </button>
          <button
            type="button"
            className="rounded-full border border-line px-3 py-1 text-ink"
            onClick={() => data && setOn(data.next)}
            disabled={!data}
          >
            Next
          </button>
          {data && !data.is_today && (
            <button
              type="button"
              className="rounded-full border border-line px-3 py-1 text-ink"
              onClick={() => setOn(null)}
            >
              Today
            </button>
          )}
        </div>
        {data?.calendar.chip && (
          <p className="rounded-full bg-wash px-3 py-1 text-sm text-ink">{data.calendar.chip}</p>
        )}
      </div>
      <h2 className="mb-4 text-2xl">{data?.date_label ?? "Calendar"}</h2>
      {day.isPending && (
        <div className="grid gap-3 sm:grid-cols-2" aria-busy="true" aria-label="Loading the day">
          <div className="h-24 animate-pulse rounded-xl bg-wash" />
          <div className="h-24 animate-pulse rounded-xl bg-wash" />
        </div>
      )}
      {data?.calendar.state === "unknown" && (
        <p className="text-muted">Calendar has not come in. This is not an empty day.</p>
      )}
      {data?.calendar.state === "empty" && (
        <p className="mb-4 text-muted">Nothing on {data.date_label}.</p>
      )}
      {data?.calendar.state === "stale" && data.day_cards.every((card) => card.events.length === 0) && (
        <p className="mb-4 text-muted">Nothing on {data.date_label} in the last snapshot.</p>
      )}
      {data && data.calendar.state !== "unknown" && <DayCards cards={data.day_cards} />}
      {data && <AddEventForm key={data.on} on={data.on} cards={data.day_cards} />}
    </section>
  );
}

function DayCards({ cards }: { cards: DayCard[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
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
                  {event.location ? <span className="text-muted"> · {event.location}</span> : null}
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}

function AddEventForm({ on, cards }: { on: string; cards: CalendarDay["day_cards"] }) {
  const queryClient = useQueryClient();
  const members = cards.filter((card) => card.member_id);
  const [title, setTitle] = useState("");
  const [startLocal, setStartLocal] = useState(`${on}T18:00`);
  const [location, setLocation] = useState("");
  const [memberId, setMemberId] = useState(members[0]?.member_id ?? "");
  const [error, setError] = useState<string | null>(null);
  const add = useMutation({
    mutationFn: api.addEvent,
    onSuccess: async () => {
      setTitle("");
      setLocation("");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["calendar-day"] });
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
