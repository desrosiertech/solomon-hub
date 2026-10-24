import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Suggestion } from "../api";

export function UseSoonList({ rows }: { rows: Suggestion[] }) {
  const queryClient = useQueryClient();
  const stop = useMutation({
    mutationFn: api.stopAsking,
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  if (rows.length === 0) {
    return <p className="text-muted">Nothing needs using soon.</p>;
  }

  return (
    <ul className="divide-y divide-line">
      {rows.map((row) => (
        <li key={row.key} className="flex items-start justify-between gap-3 py-3 first:pt-0 last:pb-0">
          <div>
            <p className="text-lg">{row.title}</p>
            <p className="text-sm text-muted">{row.detail}</p>
          </div>
          <button
            type="button"
            className="shrink-0 rounded-full border border-line px-3 py-1 text-sm text-ink disabled:opacity-50"
            onClick={() => stop.mutate(row.key)}
          >
            Stop asking about this
          </button>
        </li>
      ))}
    </ul>
  );
}
