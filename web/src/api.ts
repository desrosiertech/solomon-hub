export type InventoryItem = {
  id: string;
  label: string;
  category: string;
  storage: string;
  leftover: boolean;
  state: string;
  estimated_use_by: string;
  window_explain: string;
  window_label: string;
  closed_reason: string | null;
};

export type Suggestion = {
  key: string;
  kind: string;
  subject_id: string;
  title: string;
  detail: string;
};

export type MealIdea = {
  key: string;
  title: string;
  have: string[];
  probably_have: string[];
  check_amount: string[];
  missing: string[];
};

export type IdeasCard = {
  state: "empty" | "ready" | "stale";
  generated_at: string | null;
  now: string | null;
};

export type MealsPayload = {
  ideas: MealIdea[];
  use_soon: Suggestion[];
  ideas_card: IdeasCard;
};

export type AuditEvent = {
  id: string;
  at: string;
  actor_kind: string;
  actor_id: string;
  action: string;
  subject_type: string;
  subject_id: string;
  detail: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${path}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  provider: () => request<{ name: string }>("/api/provider"),
  clock: () => request<{ now: string }>("/api/clock"),
  setClock: (now: string) => request<{ now: string }>("/api/clock", { method: "PUT", body: JSON.stringify({ now }) }),
  settings: (body: { grace_period_minutes: number; presume_after_minutes: number }) =>
    request("/api/settings", { method: "PUT", body: JSON.stringify(body) }),
  inventory: () => request<{ items: InventoryItem[] }>("/api/inventory"),
  addItem: (body: Record<string, unknown>) =>
    request<InventoryItem>("/api/inventory", { method: "POST", body: JSON.stringify(body) }),
  home: () => request<{ ideas: MealIdea[]; use_soon: Suggestion[] }>("/api/home"),
  meals: () => request<MealsPayload>("/api/meals"),
  stopAsking: (key: string) =>
    request<void>("/api/suggestions/stop-asking", { method: "POST", body: JSON.stringify({ key }) }),
  age: () => request<{ changed: number }>("/api/jobs/age", { method: "POST" }),
  audit: () => request<{ events: AuditEvent[] }>("/api/audit"),
};
