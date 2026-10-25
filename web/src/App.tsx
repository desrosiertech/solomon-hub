import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "./api";
import { AuditPage } from "./pages/Audit";
import { CalendarPage } from "./pages/Calendar";
import { HomePage } from "./pages/Home";
import { InventoryPage } from "./pages/Inventory";
import { MealsPage } from "./pages/Meals";
import { WeatherPage } from "./pages/Weather";
import { ThemeSwitch } from "./ui/ThemeSwitch";

const TABS = [
  { id: "home", label: "Home" },
  { id: "calendar", label: "Calendar" },
  { id: "meals", label: "Meals" },
  { id: "weather", label: "Weather" },
  { id: "inventory", label: "Inventory" },
  { id: "audit", label: "History" },
] as const;

type Tab = (typeof TABS)[number]["id"];

export function App() {
  const [tab, setTab] = useState<Tab>("home");
  const provider = useQuery({ queryKey: ["provider"], queryFn: api.provider });

  return (
    <div className="min-h-screen bg-canvas font-sans text-ink">
      <header className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 pt-8 pb-6">
        <h1 className="text-4xl font-semibold tracking-tight">Solomon</h1>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm text-muted tabular-nums">
            AI: {provider.data?.name ?? "…"}
            {provider.data
              ? provider.data.signed_in
                ? " · Portal signed in"
                : " · Portal not signed in"
              : ""}
          </p>
          <ThemeSwitch />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 pb-36">
        {tab === "home" && <HomePage />}
        {tab === "calendar" && <CalendarPage />}
        {tab === "meals" && <MealsPage />}
        {tab === "weather" && <WeatherPage />}
        {tab === "inventory" && <InventoryPage />}
        {tab === "audit" && <AuditPage />}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-card">
        <div className="mx-auto flex max-w-5xl flex-wrap justify-center gap-1 px-2 py-2">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`shrink-0 rounded-full px-3 py-2 text-sm sm:text-lg ${
                tab === item.id ? "bg-wash text-ink" : "text-muted"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}
