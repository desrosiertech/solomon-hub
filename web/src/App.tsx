import { useState } from "react";
import { AuditPage } from "./pages/Audit";
import { CalendarPage } from "./pages/Calendar";
import { ChatPage } from "./pages/Chat";
import { HomePage } from "./pages/Home";
import { InventoryPage } from "./pages/Inventory";
import { MealsPage } from "./pages/Meals";
import { NewsPage } from "./pages/News";
import { SettingsPage } from "./pages/Settings";
import { SpooktoberPage } from "./pages/Spooktober";
import { WeatherPage } from "./pages/Weather";
import { RightRail } from "./ui/RightRail";

const TABS = [
  { id: "home", label: "Home" },
  { id: "calendar", label: "Calendar" },
  { id: "meals", label: "Meals" },
  { id: "weather", label: "Weather" },
  { id: "news", label: "News" },
  { id: "spooktober", label: "Spooktober" },
  { id: "inventory", label: "Inventory" },
  { id: "history", label: "History" },
  { id: "chat", label: "Chat" },
  { id: "settings", label: "Settings" },
] as const;

type Tab = (typeof TABS)[number]["id"];

export function App() {
  const [tab, setTab] = useState<Tab>("home");

  return (
    <div className="min-h-screen bg-canvas font-sans text-ink">
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 pt-5 pb-32 lg:grid-cols-[minmax(0,1fr)_17.5rem] lg:px-6">
        <div className="lg:col-start-2 lg:row-start-1">
          <RightRail />
        </div>
        <div className="lg:col-start-1 lg:row-start-1">
          <header className="mb-5">
            <h1 className="text-2xl font-semibold tracking-tight">Solomon</h1>
          </header>
          <main>
            {tab === "home" && <HomePage />}
            {tab === "calendar" && <CalendarPage />}
            {tab === "meals" && <MealsPage />}
            {tab === "weather" && <WeatherPage />}
            {tab === "news" && <NewsPage />}
            {tab === "spooktober" && <SpooktoberPage />}
            {tab === "inventory" && <InventoryPage />}
            {tab === "history" && <AuditPage />}
            {tab === "chat" && <ChatPage />}
            {tab === "settings" && <SettingsPage />}
          </main>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-card" aria-label="Primary">
        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-3 py-2">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-sm ${
                tab === item.id ? "bg-ink text-canvas" : "text-muted"
              }`}
            >
              <NavIcon id={item.id} />
              {item.label}
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}

function NavIcon({ id }: { id: Tab }) {
  const common = {
    className: "h-4 w-4",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (id === "home") {
    return (
      <svg {...common}>
        <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z" />
      </svg>
    );
  }
  if (id === "calendar") {
    return (
      <svg {...common}>
        <rect x="4" y="5" width="16" height="15" rx="2" />
        <path d="M8 3v4M16 3v4M4 10h16" />
      </svg>
    );
  }
  if (id === "meals") {
    return (
      <svg {...common}>
        <path d="M6 3v8M6 11v10M10 3v6a2 2 0 0 1-4 0M18 3c-2 2-2 4-2 8h4V3M16 11v10" />
      </svg>
    );
  }
  if (id === "weather") {
    return (
      <svg {...common}>
        <path d="M7 18h10a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.6A3.5 3.5 0 0 0 7 18z" />
      </svg>
    );
  }
  if (id === "news") {
    return (
      <svg {...common}>
        <path d="M5 5h11a2 2 0 0 1 2 2v12H7a2 2 0 0 1-2-2z" />
        <path d="M8 9h7M8 13h7" />
      </svg>
    );
  }
  if (id === "spooktober") {
    return (
      <svg {...common}>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4" />
      </svg>
    );
  }
  if (id === "inventory") {
    return (
      <svg {...common}>
        <path d="M4 8h16l-1.5 11h-13zM8 8V6a4 4 0 0 1 8 0v2" />
      </svg>
    );
  }
  if (id === "history") {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="8" />
        <path d="M12 8v5l3 2" />
      </svg>
    );
  }
  if (id === "chat") {
    return (
      <svg {...common}>
        <path d="M5 6h14v9H8l-3 3z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" />
    </svg>
  );
}
