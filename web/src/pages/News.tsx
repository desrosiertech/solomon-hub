import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Headline } from "../api";

export function NewsPage() {
  const queryClient = useQueryClient();
  const news = useQuery({ queryKey: ["news"], queryFn: api.news });
  const refresh = useMutation({
    mutationFn: api.refreshNews,
    onSuccess: (digest) => {
      queryClient.setQueryData(["news"], digest);
    },
  });
  const digest = news.data;

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl">News</h2>
        <div className="flex flex-wrap items-center gap-3">
          {digest?.chip && <Chip text={digest.chip} />}
          <button
            type="button"
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            className="rounded-full border border-line px-4 py-2 text-ink disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>
      {(news.isPending || refresh.isPending) && !digest && (
        <div className="space-y-3" aria-busy="true" aria-label="Loading the news digest">
          <div className="h-14 animate-pulse rounded-xl bg-wash" />
          <div className="h-14 animate-pulse rounded-xl bg-wash" />
          <div className="h-14 animate-pulse rounded-xl bg-wash" />
        </div>
      )}
      {news.isError && !digest && (
        <p className="text-muted">News has not come in. This is not an empty digest.</p>
      )}
      {digest?.state === "empty" && <p className="text-muted">No headlines yet.</p>}
      {digest?.state === "unknown" && (
        <p className="text-muted">News has not come in. This is not an empty digest.</p>
      )}
      {digest && (digest.state === "ready" || digest.state === "stale") && (
        <HeadlineList rows={digest.headlines} />
      )}
    </section>
  );
}

function Chip({ text }: { text: string }) {
  return <p className="rounded-full bg-wash px-3 py-1 text-sm text-ink">{text}</p>;
}

function HeadlineList({ rows }: { rows: Headline[] }) {
  if (rows.length === 0) {
    return <p className="text-muted">No headlines yet.</p>;
  }
  return (
    <ul className="divide-y divide-line">
      {rows.map((row) => (
        <li key={row.id} className="py-3 first:pt-0">
          <a
            href={row.url}
            className="text-lg text-accent underline-offset-4 hover:underline"
            rel="noopener noreferrer"
            target="_blank"
          >
            {row.title}
          </a>
          <p className="mt-1 text-sm text-muted tabular-nums">
            {row.published_label}
            {row.source_name ? ` · ${row.source_name}` : ""}
          </p>
        </li>
      ))}
    </ul>
  );
}
