import { useQuery } from "@tanstack/react-query";
import { personColor } from "../ui/person";

type PersonRating = {
  member_id: string;
  display_name: string;
  initial: string;
  rating: number | null;
  notes: string | null;
  watched_on: string;
};

type MovieEntry = {
  title: string;
  watched_on: string;
  watched_label: string;
  people: PersonRating[];
};

type Favorite = {
  title: string;
  people: string[];
};

type YearCount = {
  year: number;
  count: number;
};

type Diary = {
  empty: boolean;
  year: number;
  annual_count: number;
  favorites: Favorite[];
  recent: MovieEntry[];
  comparison: YearCount[];
};

const card = "rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]";

async function loadDiary(): Promise<Diary> {
  const response = await fetch("/api/spooktober");
  if (!response.ok) {
    throw new Error("The diary has not come in.");
  }
  return (await response.json()) as Diary;
}

function dayLabel(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, (month ?? 1) - 1, day ?? 1)));
}

function colorIndex(rows: MovieEntry[]): Map<string, number> {
  const ids = new Set<string>();
  for (const movie of rows) {
    for (const person of movie.people) {
      ids.add(person.member_id);
    }
  }
  return new Map([...ids].sort().map((id, index) => [id, index]));
}

export function SpooktoberPage() {
  const diary = useQuery({ queryKey: ["spooktober"], queryFn: loadDiary });
  const data = diary.data;

  return (
    <div className="grid gap-4">
      <section className={card}>
        <h2 className="text-2xl">Spooktober{data ? ` ${data.year}` : ""}</h2>
        {diary.isPending && (
          <div className="mt-4 h-16 animate-pulse rounded-xl bg-wash" aria-busy="true" aria-label="Loading the diary" />
        )}
        {diary.isError && <p className="mt-3 text-muted">The diary has not come in.</p>}
        {data?.empty && (
          <div className="mt-3">
            <p>The diary is empty.</p>
            <p className="mt-2 text-muted">
              Tell Solomon in chat when you watch a movie. It will show up here.
            </p>
          </div>
        )}
        {data && !data.empty && (
          <p className="mt-2">
            <span className="text-5xl font-semibold tabular-nums tracking-tight">{data.annual_count}</span>
            <span className="ml-3 text-muted">watched</span>
          </p>
        )}
      </section>

      {data && !data.empty && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <YearComparison years={data.comparison} />
            <Favorites rows={data.favorites} />
          </div>
          <Recent rows={data.recent} />
        </>
      )}
    </div>
  );
}

function YearComparison({ years }: { years: YearCount[] }) {
  const peak = Math.max(...years.map((row) => row.count), 1);
  return (
    <section className={card}>
      <h2 className="text-2xl">This year and last</h2>
      <ul className="mt-4 grid gap-4">
        {years.map((row) => (
          <li key={row.year}>
            <div className="mb-1 flex items-baseline justify-between gap-3">
              <span>{row.year}</span>
              <span className="tabular-nums text-muted">{row.count}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-wash">
              <div
                className="h-full rounded-full bg-ink"
                style={{ width: row.count === 0 ? "0%" : `${Math.max(8, (row.count / peak) * 100)}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Favorites({ rows }: { rows: Favorite[] }) {
  return (
    <section className={card}>
      <h2 className="text-2xl">Favorites</h2>
      {rows.length === 0 ? (
        <p className="mt-3 text-muted">No favorites yet.</p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {rows.map((row) => (
            <li key={row.title} className="flex items-baseline justify-between gap-3 py-3 first:pt-0 last:pb-0">
              <span className="text-lg">{row.title}</span>
              <span className="text-sm text-muted">{row.people.join(" · ")}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Recent({ rows }: { rows: MovieEntry[] }) {
  const colors = colorIndex(rows);
  return (
    <section className={card}>
      <h2 className="text-2xl">Recent</h2>
      {rows.length === 0 ? (
        <p className="mt-3 text-muted">No movies this Spooktober yet.</p>
      ) : (
        <ul className="mt-2 divide-y divide-line">
          {rows.map((movie) => (
            <li key={`${movie.title}-${movie.watched_on}`} className="py-4 first:pt-3 last:pb-0">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-lg">{movie.title}</p>
                <p className="shrink-0 text-sm text-muted">{movie.watched_label}</p>
              </div>
              <ul className="mt-3 grid gap-3">
                {movie.people.map((person) => {
                  const color = personColor(person.member_id, colors.get(person.member_id) ?? 0);
                  return (
                    <li key={`${person.member_id}-${person.watched_on}`} className="flex items-start gap-3">
                      <span
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-semibold text-white"
                        style={{ backgroundColor: color }}
                      >
                        {person.initial}
                      </span>
                      <div>
                        <p>
                          {person.display_name}
                          <Rating rating={person.rating} />
                        </p>
                        {person.notes && <p className="text-sm text-muted">{person.notes}</p>}
                        {person.watched_on !== movie.watched_on && (
                          <p className="text-sm text-muted">{dayLabel(person.watched_on)}</p>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Rating({ rating }: { rating: number | null }) {
  if (rating == null) {
    return <span className="ml-2 text-sm text-muted">No rating</span>;
  }
  return (
    <span className="ml-2 inline-flex items-center gap-1 align-middle" aria-label={`${rating} out of 5`}>
      <span className="tabular-nums">{rating}</span>
      <span className="inline-flex gap-0.5" aria-hidden="true">
        {Array.from({ length: 5 }, (_, index) => (
          <span key={index} className={`h-1.5 w-1.5 rounded-full ${index < rating ? "bg-ink" : "bg-wash"}`} />
        ))}
      </span>
    </span>
  );
}
