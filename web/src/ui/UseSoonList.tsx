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
    <ul className="space-y-3">
      {rows.map((row) => (
        <li key={row.key} className="flex items-start justify-between gap-3 rounded-xl bg-sand-soft/80 px-4 py-3">
          <div>
            <p className="text-lg">{row.title}</p>
            <p className="text-sm text-muted">{row.detail}</p>
          </div>
          <button
            type="button"
            className="shrink-0 rounded-full border border-line bg-card px-3 py-1 text-sm"
            onClick={() => stop.mutate(row.key)}
          >
            Stop asking about this
          </button>
        </li>
      ))}
    </ul>
  );
}
