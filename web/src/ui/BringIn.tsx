import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { ApiError, api, ReceiptLine, RecipeCard } from "../api";

const STORAGE = ["fridge", "pantry", "freezer", "counter"] as const;

function message(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail;
  }
  return "That did not go through.";
}

export function BringIn() {
  const queryClient = useQueryClient();
  const recipes = useQuery({ queryKey: ["recipes"], queryFn: api.recipes });
  const nights = useQuery({ queryKey: ["planned"], queryFn: api.plannedMeals });
  const [lines, setLines] = useState<ReceiptLine[] | null>(null);
  const [receiptId, setReceiptId] = useState<string | null>(null);
  const [card, setCard] = useState<RecipeCard | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState<"screenshot" | "book_photo">("screenshot");
  const [on, setOn] = useState("");
  const [recipeId, setRecipeId] = useState("");

  const receipt = useMutation({
    mutationFn: (image: File) => api.submitReceipt(image),
    onSuccess: (proposal) => {
      setNote(null);
      setReceiptId(proposal.id);
      setLines(proposal.lines);
    },
    onError: (error) => setNote(message(error)),
  });
  const apply = useMutation({
    mutationFn: () =>
      api.applyReceipt(
        receiptId ?? "",
        (lines ?? []).filter((line) => line.food).map((line) => ({ id: line.id, storage: line.storage })),
      ),
    onSuccess: async () => {
      setLines(null);
      setReceiptId(null);
      setNote("Added to inventory.");
      await queryClient.invalidateQueries();
    },
    onError: (error) => setNote(message(error)),
  });
  const recipe = useMutation({
    mutationFn: (input: { url?: string; image?: File; kind?: "screenshot" | "book_photo" }) => {
      if (input.url) {
        return api.proposeRecipeUrl(input.url);
      }
      return api.proposeRecipeImage(input.kind ?? "screenshot", input.image as File);
    },
    onSuccess: (next) => {
      setNote(null);
      setCard(next);
    },
    onError: (error) => setNote(message(error)),
  });
  const accept = useMutation({
    mutationFn: () => api.acceptRecipe(card?.id ?? ""),
    onSuccess: async () => {
      setCard(null);
      setNote("Banked for later weeks.");
      await queryClient.invalidateQueries();
    },
    onError: (error) => setNote(message(error)),
  });
  const plan = useMutation({
    mutationFn: () => api.planNight(on, recipeId),
    onSuccess: async () => {
      setNote("Planned.");
      await queryClient.invalidateQueries();
    },
    onError: (error) => setNote(message(error)),
  });

  function onReceipt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get("image");
    if (file instanceof File && file.size > 0) {
      receipt.mutate(file);
    }
  }

  function onRecipeFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get("image");
    if (file instanceof File && file.size > 0) {
      recipe.mutate({ image: file, kind });
    }
  }

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <h2 className="text-2xl">Receipts and recipes</h2>
      <p className="mb-4 text-sm text-muted">
        A receipt photo becomes inventory after one tap. A screenshot, a book photo, or a link
        becomes a recipe you can plan into a later week.
      </p>
      {note && <p className="mb-3 text-sm">{note}</p>}

      <form onSubmit={onReceipt} className="space-y-3 border-t border-line py-4">
        <label className="block text-sm text-muted">
          Receipt photo
          <input name="image" type="file" accept="image/*" className="mt-1 block w-full text-ink" />
        </label>
        <button type="submit" className="rounded-full bg-accent px-4 py-2 text-on-accent">
          Read receipt
        </button>
      </form>
      {lines && (
        <div className="space-y-3 pb-4">
          <ul className="divide-y divide-line">
            {lines.map((line) => (
              <li key={line.id} className="flex items-center justify-between gap-3 py-3">
                <span>
                  {line.label}
                  {line.food ? "" : " · not food"}
                </span>
                {line.food && (
                  <select
                    value={line.storage}
                    onChange={(event) =>
                      setLines(
                        lines.map((item) =>
                          item.id === line.id ? { ...item, storage: event.target.value } : item,
                        ),
                      )
                    }
                    className="rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
                  >
                    {STORAGE.map((place) => (
                      <option key={place} value={place}>
                        {place}
                      </option>
                    ))}
                  </select>
                )}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="rounded-full bg-accent px-4 py-2 text-on-accent"
            onClick={() => apply.mutate()}
          >
            Add to inventory
          </button>
        </div>
      )}

      <form onSubmit={onRecipeFile} className="space-y-3 border-t border-line py-4">
        <label className="block text-sm text-muted">
          Recipe photo
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value as "screenshot" | "book_photo")}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          >
            <option value="screenshot">Screenshot</option>
            <option value="book_photo">Book photo</option>
          </select>
        </label>
        <input name="image" type="file" accept="image/*" className="block w-full text-ink" />
        <button type="submit" className="rounded-full border border-line px-4 py-2">
          Read photo
        </button>
      </form>

      <form
        className="space-y-3 border-t border-line py-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (url) {
            recipe.mutate({ url });
          }
        }}
      >
        <label className="block text-sm text-muted">
          Recipe link
          <input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://"
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          />
        </label>
        <button type="submit" className="rounded-full border border-line px-4 py-2">
          Read link
        </button>
      </form>
      {card && (
        <div className="space-y-2 pb-4">
          <p className="text-lg font-medium">{card.title}</p>
          <p className="text-sm text-muted">{card.ingredients.join(", ")}</p>
          <p>{card.steps.join(" ")}</p>
          <button
            type="button"
            className="rounded-full bg-accent px-4 py-2 text-on-accent"
            onClick={() => accept.mutate()}
          >
            Bank recipe
          </button>
        </div>
      )}

      <form
        className="space-y-3 border-t border-line pt-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (on && recipeId) {
            plan.mutate();
          }
        }}
      >
        <h3 className="text-lg">Plan a night</h3>
        <label className="block text-sm text-muted">
          Date
          <input
            type="date"
            value={on}
            onChange={(event) => setOn(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          />
        </label>
        <label className="block text-sm text-muted">
          Recipe
          <select
            value={recipeId}
            onChange={(event) => setRecipeId(event.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
          >
            <option value="">Choose</option>
            {recipes.data?.recipes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-full border border-line px-4 py-2">
          Plan this night
        </button>
        {nights.data && nights.data.nights.length > 0 && (
          <ul className="divide-y divide-line">
            {nights.data.nights.map((night) => (
              <li key={night.on} className="py-2 text-sm">
                {night.on} · {night.title}
              </li>
            ))}
          </ul>
        )}
      </form>
    </section>
  );
}
