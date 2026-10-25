import type { Suggestion } from "../api";

export function UseSoonList({ rows }: { rows: Suggestion[] }) {
  if (rows.length === 0) {
    return <p className="text-muted">Nothing needs using soon.</p>;
  }

  return (
    <ul className="divide-y divide-line">
      {rows.map((row) => (
        <li key={row.key} className="py-3 first:pt-0 last:pb-0">
          <p className="text-lg">{row.title}</p>
          <p className="text-sm text-muted">{row.detail}</p>
        </li>
      ))}
    </ul>
  );
}
