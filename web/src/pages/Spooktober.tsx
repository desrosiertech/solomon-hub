import { useQuery } from "@tanstack/react-query";
import { personColor } from "../ui/person";

type PersonRating = {
  member_id: string;
  display_name: string;
  initial: string;
  rating: number | null;
  spook: number | null;
  notes: string | null;
  watched_on: string;
};

type MovieEntry = {
  title: string;
  watched_on: string;
  watched_label: string;
  best_of: boolean;
  people: PersonRating[];
};

type YearCount = {
  year: number;
  count: number;
};

type Diary = {
  empty: boolean;
  year: number;
  chart: YearCount[];
  movies: MovieEntry[];
  best_of: MovieEntry[];
};

const card = "rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]";
const PEOPLE = ["member-desrosier", "member-peter"];

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

function colorFor(memberId: string): string {
  const index = PEOPLE.indexOf(memberId);
  return personColor(memberId, index < 0 ? 0 : index);
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
        {data && !data.empty && <p className="mt-2 text-muted">What we watched, and the ones we kept.</p>}
      </section>

      {data && !data.empty && (
        <>
          <YearChart years={data.chart} />
          <MovieSection title="Every movie" movies={data.movies} empty="No movies in the diary yet." />
          <MovieSection title="Best of" movies={data.best_of} empty="No best-of picks yet." />
        </>
      )}
    </div>
  );
}

function YearChart({ years }: { years: YearCount[] }) {
  const peak = Math.max(...years.map((row) => row.count), 1);
  return (
    <section className={card}>
      <h2 className="text-2xl">Movies by year</h2>
      <ul className="mt-4 flex items-end gap-3" aria-label="Movies watched each year">
        {years.map((row) => {
          const height = row.count === 0 ? 2 : Math.max(18, Math.round((row.count / peak) * 144));
          return (
            <li key={row.year} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <span className="text-sm tabular-nums">{row.count}</span>
              <div className="flex h-36 w-full items-end justify-center">
                <div className="flex h-full w-full max-w-14 items-end rounded-t-lg bg-wash">
                  <div
                    className={`w-full rounded-t-lg ${row.count === 0 ? "bg-line" : "bg-ink"}`}
                    style={{ height: `${height}px` }}
                    aria-label={`${row.year}: ${row.count} movies`}
                  />
                </div>
              </div>
              <span className="text-sm text-muted tabular-nums">{row.year}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function MovieSection({ title, movies, empty }: { title: string; movies: MovieEntry[]; empty: string }) {
  return (
    <section className={card}>
      <h2 className="text-2xl">{title}</h2>
      {movies.length === 0 ? (
        <p className="mt-3 text-muted">{empty}</p>
      ) : (
        <ul className="mt-2 divide-y divide-line">
          {movies.map((movie) => (
            <li key={`${title}-${movie.title}`} className="py-4 first:pt-3 last:pb-0">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                <p className="text-lg">{movie.title}</p>
                <p className="text-sm text-muted">
                  {movie.watched_label}, {movie.watched_on.slice(0, 4)}
                </p>
              </div>
              <ul className="mt-3 grid gap-3">
                {movie.people.map((person) => (
                  <PersonRow key={person.member_id} person={person} movieDate={movie.watched_on} />
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function PersonRow({ person, movieDate }: { person: PersonRating; movieDate: string }) {
  const color = colorFor(person.member_id);
  const rating = person.rating == null ? "no rating" : `${person.rating} out of 10`;
  const spook = person.spook == null ? "no spook rating" : `spook ${person.spook} out of 10`;
  return (
    <li className="flex items-start gap-3">
      <span
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-semibold text-white"
        style={{ backgroundColor: color }}
      >
        {person.initial}
      </span>
      <div className="min-w-0">
        <p>{person.display_name}</p>
        <p className="mt-0.5 flex flex-wrap gap-x-3 text-sm tabular-nums" aria-label={`${person.display_name}, ${rating}, ${spook}`}>
          <span>
            {person.rating ?? "—"} <span className="text-muted">/ 10</span>
          </span>
          <span className="text-muted">Spook {person.spook ?? "—"} / 10</span>
        </p>
        {person.notes && <p className="text-sm text-muted">{person.notes}</p>}
        {person.watched_on !== movieDate && <p className="text-sm text-muted">{dayLabel(person.watched_on)}</p>}
      </div>
    </li>
  );
}
