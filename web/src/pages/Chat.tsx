import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { ApiError, api } from "../api";

export function ChatPage() {
  const queryClient = useQueryClient();
  const thread = useQuery({ queryKey: ["chat"], queryFn: api.chat });
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const send = useMutation({
    mutationFn: () => api.sendChat(text, image ?? undefined),
    onSuccess: async () => {
      setText("");
      setImage(null);
      if (preview) {
        URL.revokeObjectURL(preview);
      }
      setPreview(null);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["chat"] });
    },
    onError: (reason: unknown) => {
      setError(reason instanceof ApiError ? reason.detail : "That message did not send.");
    },
  });

  function onPhoto(file: File | null) {
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setImage(file);
    setPreview(file ? URL.createObjectURL(file) : null);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() && !image) {
      setError("Say something or attach a photo.");
      return;
    }
    send.mutate();
  }

  const messages = thread.data?.messages ?? [];

  return (
    <div className="grid gap-4">
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Chat</h2>
        <p className="mt-1 text-sm text-muted">
          An event, a grocery correction, a recipe, a screenshot, or a receipt photo goes here.
        </p>
        {thread.isPending && <p className="mt-4 text-muted">Loading chat…</p>}
        {thread.data && messages.length === 0 && (
          <p className="mt-6 text-muted">Nothing sent yet. Solomon keeps each message on this screen.</p>
        )}
        {messages.length > 0 && (
          <ol className="mt-4 space-y-3">
            {messages.map((message) => (
              <li key={message.id} className="rounded-2xl border border-line bg-canvas px-4 py-3">
                {message.text && <p className="text-lg">{message.text}</p>}
                {message.image_url && (
                  <img
                    src={message.image_url}
                    alt="Attached photo"
                    className="mt-2 max-h-56 rounded-xl border border-line"
                  />
                )}
                <p className="mt-2 text-sm text-muted">{message.proposal.summary}</p>
              </li>
            ))}
          </ol>
        )}
      </section>

      <form
        onSubmit={onSubmit}
        className="rounded-2xl border border-line bg-card p-4 shadow-[0_16px_40px_-28px_var(--shadow)]"
      >
        <label className="block text-sm text-muted" htmlFor="chat-text">
          Message
        </label>
        <textarea
          id="chat-text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={3}
          placeholder="An event, a correction, a recipe, or a receipt."
          className="mt-1 w-full resize-y rounded-xl border border-line bg-canvas px-3 py-2 text-ink"
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="rounded-full border border-line px-4 py-2 text-sm">
            Photo
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="sr-only"
              onChange={(event) => onPhoto(event.target.files?.[0] ?? null)}
            />
          </label>
          {image && <span className="text-sm text-muted">{image.name}</span>}
          <button
            type="submit"
            disabled={send.isPending}
            className="ml-auto rounded-full bg-accent px-4 py-2 text-on-accent disabled:opacity-50"
          >
            Send
          </button>
        </div>
        {preview && (
          <img src={preview} alt="Photo to send" className="mt-3 max-h-40 rounded-xl border border-line" />
        )}
        {error && <p className="mt-3 text-sm text-muted">{error}</p>}
      </form>
    </div>
  );
}
