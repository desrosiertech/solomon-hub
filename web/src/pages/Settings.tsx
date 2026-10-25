import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api";
import { Household } from "../settings/Household";
import { ThemeSwitch } from "../ui/ThemeSwitch";

export function SettingsPage() {
  const provider = useQuery({ queryKey: ["provider"], queryFn: api.provider });
  const connections = useQuery({ queryKey: ["connections"], queryFn: api.connections });
  const providerLine = provider.data
    ? `AI: ${provider.data.name}${provider.data.signed_in ? " · Portal signed in" : " · Portal not signed in"}`
    : "AI: …";

  return (
    <div className="grid gap-4">
      <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
        <h2 className="text-2xl">Theme</h2>
        <p className="mt-1 mb-4 text-sm text-muted">Light, navy, or dark. This screen remembers the choice.</p>
        <ThemeSwitch />
      </section>
      <ConnectionCard
        title="Calendar"
        connected={connections.data?.calendar.connected === true}
        note="Google Calendar can be connected here later. This screen does not take a password or a token."
      />
      <ConnectionCard
        title="API"
        connected={connections.data?.api.connected === true}
        note="A model API can be connected here later. This screen does not take a key or a token."
        detail={providerLine}
      />
      <Household />
    </div>
  );
}

function ConnectionCard({
  title,
  connected,
  note,
  detail,
}: {
  title: string;
  connected: boolean;
  note: string;
  detail?: string;
}) {
  const [showPlace, setShowPlace] = useState(false);

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl">{title}</h2>
          <p className="mt-1 text-muted">{connected ? "Connected" : "Not connected"}</p>
          {detail && <p className="mt-1 text-sm text-muted tabular-nums">{detail}</p>}
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={connected}
          aria-label={`${title} connection`}
          onClick={() => setShowPlace(true)}
          className="relative mt-1 h-7 w-12 shrink-0 rounded-full border border-line bg-wash"
        >
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-card shadow ${
              connected ? "right-0.5" : "left-0.5"
            }`}
          />
        </button>
      </div>
      <button
        type="button"
        className="mt-4 rounded-full border border-line px-4 py-2 text-sm"
        onClick={() => setShowPlace(true)}
      >
        Connect later
      </button>
      {showPlace && <p className="mt-3 text-sm text-muted">{note}</p>}
    </section>
  );
}
