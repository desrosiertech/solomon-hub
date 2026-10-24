import type { MealIdea } from "../api";

export function IdeasList({ ideas }: { ideas: MealIdea[] }) {
  if (ideas.length === 0) {
    return <p className="text-muted">No dinners from what we have right now.</p>;
  }
  return (
    <ul className="space-y-3">
      {ideas.map((idea) => (
        <li key={idea.key} className="rounded-xl bg-sage-soft/60 px-4 py-3">
          <p className="text-lg font-medium">{idea.title}</p>
          {idea.have.length > 0 && (
            <p className="text-sm text-muted">Have: {idea.have.join(", ")}</p>
          )}
          {idea.probably_have.length > 0 && (
            <p className="text-sm text-muted">Probably have: {idea.probably_have.join(", ")}</p>
          )}
          {idea.check_amount.length > 0 && (
            <p className="text-sm text-muted">Check amount: {idea.check_amount.join(", ")}</p>
          )}
          {idea.missing.length > 0 && (
            <p className="text-sm text-muted">Need: {idea.missing.join(", ")}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
