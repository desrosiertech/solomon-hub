import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApiError, api, type HouseholdDraft } from "../api";

const fieldClass = "w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink";

export function Household() {
  const queryClient = useQueryClient();
  const household = useQuery({ queryKey: ["household"], queryFn: api.household });
  const [draft, setDraft] = useState<HouseholdDraft | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const form = draft ?? household.data ?? null;

  const save = useMutation({
    mutationFn: api.saveHousehold,
    onSuccess: async (saved) => {
      setDraft(saved);
      setNote("Saved");
      await queryClient.invalidateQueries({ queryKey: ["household"] });
    },
    onError: () => setNote(null),
  });

  if (household.isPending) {
    return <p className="text-muted">Loading household preferences…</p>;
  }
  if (household.isError || form === null) {
    return <p className="text-muted">Household preferences did not load.</p>;
  }

  function update(patch: Partial<HouseholdDraft>) {
    setDraft({ ...(draft ?? household.data)!, ...patch });
    setNote(null);
  }

  const error = save.error instanceof ApiError ? save.error.detail : null;

  return (
    <>
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Adults</h2>
        <p className="mt-1 mb-4 text-sm text-muted">
          Display names for the adults. Placeholders, with no login.
        </p>
        <div className="space-y-2">
          {form.adults.map((adult, index) => (
            <div key={adult.id ?? `new-${index}`} className="flex gap-2">
              <input
                aria-label={`Adult ${index + 1} display name`}
                value={adult.display_name}
                onChange={(event) => {
                  const adults = form.adults.slice();
                  adults[index] = { ...adult, display_name: event.target.value };
                  update({ adults });
                }}
                className={fieldClass}
              />
              <button
                type="button"
                className="shrink-0 rounded-full border border-line px-4 py-2 text-sm disabled:opacity-40"
                disabled={form.adults.length === 1}
                onClick={() => update({ adults: form.adults.filter((_, item) => item !== index) })}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          className="mt-3 rounded-full border border-line px-4 py-2 text-sm"
          onClick={() => update({ adults: [...form.adults, { display_name: "" }] })}
        >
          Add an adult
        </button>
      </section>

      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Pantry</h2>
        <p className="mt-1 mb-4 text-sm text-muted">
          Storage, estimated use-by windows, and what happens when food is presumed discarded.
        </p>
        <h3 className="mb-2 text-sm text-muted">Storage locations</h3>
        <PhraseList
          label="Storage location"
          phrases={form.storage_locations}
          allowEmpty={false}
          addLabel="Add a location"
          onChange={(storage_locations) => update({ storage_locations })}
        />
        <div className="mt-5 border-t border-line pt-4">
          <h3 className="mb-2 text-sm text-muted">Estimated use-by windows</h3>
          <p className="mb-3 text-sm text-muted">A freshness estimate for the household.</p>
          <Choice
            label="Freshness"
            value={form.freshness}
            options={[
              { id: "conservative", label: "Conservative" },
              { id: "permissive", label: "Permissive" },
            ]}
            onChange={(freshness) => update({ freshness })}
          />
        </div>
        <label className="mt-5 block border-t border-line pt-4 text-sm text-muted">
          Dismissal suppression (days)
          <input
            type="number"
            min={1}
            max={365}
            value={form.suppression_days}
            aria-label="Dismissal suppression days"
            onChange={(event) => update({ suppression_days: Number(event.target.value) })}
            className={`mt-1 ${fieldClass}`}
          />
          <span className="mt-1 block">How long a dismissed suggestion stays quiet.</span>
        </label>
        <div className="mt-5 border-t border-line pt-4">
          <h3 className="mb-2 text-sm text-muted">Presumed discarded</h3>
          <Choice
            label="Presumed discarded"
            value={form.presumed_discard}
            options={[
              { id: "archive", label: "Archive" },
              { id: "review", label: "Review" },
            ]}
            onChange={(presumed_discard) => update({ presumed_discard })}
          />
          <p className="mt-2 text-sm text-muted">
            Archive records the presumption. Review holds the item as stale.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Serving size</h2>
        <label className="mt-3 block text-sm text-muted">
          Household serving size
          <input
            type="number"
            min={1}
            max={24}
            value={form.serving_size}
            aria-label="Household serving size"
            onChange={(event) => update({ serving_size: Number(event.target.value) })}
            className={`mt-1 max-w-xs ${fieldClass}`}
          />
        </label>
      </section>

      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">News topics</h2>
        <p className="mt-1 mb-4 text-sm text-muted">A list of phrases for the digest.</p>
        {form.news_topics.length === 0 && <p className="mb-3 text-muted">No topics yet.</p>}
        <PhraseList
          label="News topic"
          phrases={form.news_topics}
          allowEmpty
          addLabel="Add a topic"
          onChange={(news_topics) => update({ news_topics })}
        />
        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
          <button
            type="button"
            className="rounded-full bg-accent px-4 py-2 text-on-accent disabled:opacity-50"
            disabled={save.isPending}
            onClick={() => save.mutate(form)}
          >
            Save household preferences
          </button>
          {note && <p className="text-sm text-muted">{note}</p>}
          {error && <p className="text-sm text-muted">{error}</p>}
        </div>
      </section>
    </>
  );
}

function PhraseList({
  label,
  phrases,
  allowEmpty,
  addLabel,
  onChange,
}: {
  label: string;
  phrases: string[];
  allowEmpty: boolean;
  addLabel: string;
  onChange: (phrases: string[]) => void;
}) {
  return (
    <div className="space-y-2">
      {phrases.map((phrase, index) => (
        <div key={`${label}-${index}`} className="flex gap-2">
          <input
            aria-label={`${label} ${index + 1}`}
            value={phrase}
            onChange={(event) => {
              const next = phrases.slice();
              next[index] = event.target.value;
              onChange(next);
            }}
            className={fieldClass}
          />
          <button
            type="button"
            className="shrink-0 rounded-full border border-line px-4 py-2 text-sm disabled:opacity-40"
            disabled={!allowEmpty && phrases.length === 1}
            onClick={() => onChange(phrases.filter((_, item) => item !== index))}
          >
            Remove
          </button>
        </div>
      ))}
      <button
        type="button"
        className="rounded-full border border-line px-4 py-2 text-sm"
        onClick={() => onChange([...phrases, ""])}
      >
        {addLabel}
      </button>
    </div>
  );
}

function Choice<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { id: T; label: string }[];
  onChange: (id: T) => void;
}) {
  return (
    <div className="flex w-fit flex-wrap rounded-full border border-line p-1" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          aria-pressed={value === option.id}
          onClick={() => onChange(option.id)}
          className={`rounded-full px-3 py-1 text-sm ${
            value === option.id ? "bg-accent text-on-accent" : "text-muted"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
