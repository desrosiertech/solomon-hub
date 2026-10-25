import type { DayCard } from "../api";
import { personColor } from "./person";

export function DayCards({ cards }: { cards: DayCard[] }) {
  let memberIndex = 0;
  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {cards.map((card) => {
        const color = personColor(card.member_id, memberIndex);
        if (card.member_id) {
          memberIndex += 1;
        }
        return (
          <li
            key={card.member_id ?? "everyone"}
            className="overflow-hidden rounded-2xl border border-line bg-card shadow-[0_16px_40px_-28px_var(--shadow)]"
          >
            <div className="flex items-center gap-3 px-4 py-3 text-white" style={{ backgroundColor: color }}>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-white/25 text-sm font-semibold">
                {card.initial}
              </span>
              <span className="text-lg font-semibold">{card.display_name}</span>
            </div>
            <div className="px-4 py-3">
              {card.events.length === 0 ? (
                <p className="text-muted">—</p>
              ) : (
                <ul className="divide-y divide-line">
                  {card.events.map((event) => (
                    <li key={event.id} className="py-2 first:pt-0 last:pb-0">
                      <p className="text-lg">{event.title}</p>
                      <p className="text-sm text-muted">
                        {event.when_label}
                        {event.location ? ` · ${event.location}` : ""}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
