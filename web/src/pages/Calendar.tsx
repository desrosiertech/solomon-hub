import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { DayCards } from "../ui/DayCards";

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
            <button type="button" className="rounded-full border border-line px-3 py-1 text-ink" onClick={() => setOn(null)}>
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
      {data?.calendar.state === "empty" && <p className="text-muted">Nothing on {data.date_label}.</p>}
      {data?.calendar.state === "stale" && data.day_cards.every((card) => card.events.length === 0) && (
        <p className="mb-4 text-muted">Nothing on {data.date_label} in the last snapshot.</p>
      )}
      {data && data.calendar.state !== "unknown" && <DayCards cards={data.day_cards} />}
    </section>
  );
}
