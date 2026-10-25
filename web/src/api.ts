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

export type WeatherForecast = WeatherSnapshot & {
  place: string;
  date_label: string;
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

export type Headline = {
  id: string;
  title: string;
  url: string;
  published_at: string;
  published_label: string;
  source_name: string | null;
};

export type NewsDigest = SourceCard & {
  headlines: Headline[];
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

export type HouseholdAdult = {
  id: string;
  display_name: string;
};

export type HouseholdPreferences = {
  adults: HouseholdAdult[];
  storage_locations: string[];
  freshness: "conservative" | "permissive";
  suppression_days: number;
  presumed_discard: "archive" | "review";
  serving_size: number;
  news_topics: string[];
};

export type HouseholdDraft = Omit<HouseholdPreferences, "adults"> & {
  adults: { id?: string; display_name: string }[];
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

export type ChatProposal = {
  status: "reader_off" | "proposed";
  kind: string | null;
  summary: string;
};

export type ChatMessage = {
  id: string;
  text: string;
  has_image: boolean;
  image_url: string | null;
  at: string;
  proposal: ChatProposal;
};

export type ConnectionSide = {
  connected: boolean;
  state: "not_connected";
};

export type Connections = {
  calendar: ConnectionSide;
  api: ConnectionSide;
};

export type VetRecord = {
  id: string;
  date: string | null;
  kind: string;
  evidence_note: string | null;
  next_due?: string;
};

export type HouseholdDog = {
  id: string;
  name: string;
  missing: string[];
  ask: string | null;
  records: VetRecord[];
};

export type DogsExport = {
  dogs: HouseholdDog[];
};

export class ApiError extends Error {
  detail: string;

  constructor(detail: string) {
    super(detail);
    this.detail = detail;
  }
}

export type CarMaintenance = {
  id: string;
  kind: string;
  kind_label: string;
  performed_on: string | null;
  evidence_note: string | null;
  next_due?: string;
};

export type HouseholdCar = {
  id: string;
  nickname: string | null;
  maintenance: CarMaintenance[];
  missing: string[];
};

export type CarsPayload = {
  cars: HouseholdCar[];
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
  household: () => request<HouseholdPreferences>("/api/household"),
  saveHousehold: (body: HouseholdDraft) =>
    request<HouseholdPreferences>("/api/household", {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  clock: () => request<{ now: string }>("/api/clock"),
  setClock: (now: string) => request<{ now: string }>("/api/clock", { method: "PUT", body: JSON.stringify({ now }) }),
  settings: (body: { grace_period_minutes: number; presume_after_minutes: number }) =>
    request("/api/settings", { method: "PUT", body: JSON.stringify(body) }),
  inventory: () => request<{ items: InventoryItem[] }>("/api/inventory"),
  addItem: (body: Record<string, unknown>) =>
    request<InventoryItem>("/api/inventory", { method: "POST", body: JSON.stringify(body) }),
  home: () => request<HomePayload>("/api/home"),
  weather: () => request<WeatherForecast>("/api/weather"),
  refreshWeather: () => request<WeatherSnapshot>("/api/weather/refresh", { method: "POST" }),
  calendarDay: (on?: string | null) =>
    request<CalendarDay>(`/api/calendar/day${on ? `?on=${encodeURIComponent(on)}` : ""}`),
  news: () => request<NewsDigest>("/api/news"),
  refreshNews: () => request<NewsDigest>("/api/news/refresh", { method: "POST" }),
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
  cars: () => request<CarsPayload>("/api/cars"),
  chat: () => request<{ messages: ChatMessage[] }>("/api/chat"),
  sendChat: (text: string, image?: File) => {
    if (image) {
      const body = new FormData();
      body.append("text", text);
      body.append("image", image);
      return sendForm<ChatMessage>("/api/chat", body);
    }
    return request<ChatMessage>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  },
  connections: () => request<Connections>("/api/connections"),
  dogs: () => request<DogsExport>("/api/dogs"),
};
