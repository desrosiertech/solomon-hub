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

export type CalendarEntry = {
  id: string;
  title: string;
  when_label: string;
  location: string | null;
  who: string;
  initial: string;
  member_id: string | null;
};

export type DayCard = {
  member_id: string | null;
  display_name: string;
  initial: string;
  events: CalendarEntry[];
};

export type SourceCard = {
  state: "empty" | "ready" | "stale" | "unknown";
  chip: string | null;
  updated_at: string | null;
};

export type WeatherSnapshot = SourceCard & {
  temp_f: number | null;
  high_f: number | null;
  low_f: number | null;
  summary: string | null;
};

export type CalendarDay = {
  on: string;
  date_label: string;
  prev: string;
  next: string;
  is_today: boolean;
  day_cards: DayCard[];
  calendar: SourceCard;
};

export type HomePayload = {
  ideas: MealIdea[];
  use_soon: Suggestion[];
  now: string;
  date_label: string;
  up_next: CalendarEntry[];
  day_cards: DayCard[];
  calendar: SourceCard;
  weather: WeatherSnapshot;
};

export type IdeasCard = {
  state: "empty" | "ready" | "stale";
  generated_at: string | null;
  now: string | null;
};

export type ReaderStatus = {
  on: boolean;
  label: string;
};

export type MealsPayload = {
  ideas: MealIdea[];
  use_soon: Suggestion[];
  ideas_card: IdeasCard;
  reader: ReaderStatus;
};

export type ProviderStatus = {
  name: string;
  signed_in: boolean;
  reachable: boolean;
};

export type ReceiptLine = {
  id: string;
  label: string;
  category: string;
  storage: string;
  food: boolean;
};

export type ReceiptProposal = {
  id: string;
  lines: ReceiptLine[];
};

export type RecipeCard = {
  id: string;
  title: string;
  source_kind?: string;
  source_url?: string | null;
  ingredients: string[];
  steps: string[];
  status?: string;
};

export type PlannedNight = {
  on: string;
  recipe_id: string;
  title: string;
};

export class ApiError extends Error {
  detail: string;

  constructor(detail: string) {
    super(detail);
    this.detail = detail;
  }
}

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
    let detail = `${response.status} ${path}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      /* keep the status line */
    }
    throw new ApiError(detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function sendForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(path, { method: "POST", body });
  if (!response.ok) {
    let detail = `${response.status} ${path}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      /* keep the status line */
    }
    throw new ApiError(detail);
  }
  return (await response.json()) as T;
}

export const api = {
  provider: () => request<ProviderStatus>("/api/provider"),
  clock: () => request<{ now: string }>("/api/clock"),
  setClock: (now: string) => request<{ now: string }>("/api/clock", { method: "PUT", body: JSON.stringify({ now }) }),
  settings: (body: { grace_period_minutes: number; presume_after_minutes: number }) =>
    request("/api/settings", { method: "PUT", body: JSON.stringify(body) }),
  inventory: () => request<{ items: InventoryItem[] }>("/api/inventory"),
  addItem: (body: Record<string, unknown>) =>
    request<InventoryItem>("/api/inventory", { method: "POST", body: JSON.stringify(body) }),
  home: () => request<HomePayload>("/api/home"),
  calendarDay: (on?: string | null) =>
    request<CalendarDay>(`/api/calendar/day${on ? `?on=${encodeURIComponent(on)}` : ""}`),
  addEvent: (body: {
    title: string;
    start_local: string;
    location?: string;
    member_id?: string | null;
  }) => request<CalendarEntry>("/api/calendar/events", { method: "POST", body: JSON.stringify(body) }),
  meals: () => request<MealsPayload>("/api/meals"),
  stopAsking: (key: string) =>
    request<void>("/api/suggestions/stop-asking", { method: "POST", body: JSON.stringify({ key }) }),
  age: () => request<{ changed: number }>("/api/jobs/age", { method: "POST" }),
  audit: () => request<{ events: AuditEvent[] }>("/api/audit"),
  submitReceipt: (image: File) => {
    const body = new FormData();
    body.append("image", image);
    return sendForm<ReceiptProposal>("/api/receipts", body);
  },
  applyReceipt: (id: string, lines: { id: string; storage: string }[]) =>
    request<{ added: number }>(`/api/receipts/${id}/apply`, {
      method: "POST",
      body: JSON.stringify({ lines }),
    }),
  proposeRecipeUrl: (url: string) =>
    request<RecipeCard>("/api/recipes/proposals", {
      method: "POST",
      body: JSON.stringify({ source_kind: "url", url }),
    }),
  proposeRecipeImage: (sourceKind: "screenshot" | "book_photo", image: File) => {
    const body = new FormData();
    body.append("source_kind", sourceKind);
    body.append("image", image);
    return sendForm<RecipeCard>("/api/recipes/proposals", body);
  },
  acceptRecipe: (id: string) =>
    request<RecipeCard>(`/api/recipes/proposals/${id}/accept`, { method: "POST" }),
  recipes: () => request<{ recipes: RecipeCard[] }>("/api/recipes"),
  planNight: (on: string, recipeId: string) =>
    request<PlannedNight>("/api/planned-meals", {
      method: "POST",
      body: JSON.stringify({ on, recipe_id: recipeId }),
    }),
  plannedMeals: () => request<{ nights: PlannedNight[] }>("/api/planned-meals"),
};
