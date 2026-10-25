import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type WeatherForecast } from "../api";

export function WeatherPage() {
  const queryClient = useQueryClient();
  const weather = useQuery({ queryKey: ["weather"], queryFn: api.weather });
  const refresh = useMutation({
    mutationFn: api.refreshWeather,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["weather"] });
      await queryClient.invalidateQueries({ queryKey: ["home"] });
    },
  });
  const data = weather.data;

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl">Weather</h2>
          <p className="mt-1 text-muted">{data ? `${data.place} · ${data.date_label}` : "Home"}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {data?.chip && <p className="rounded-full bg-wash px-3 py-1 text-sm text-ink">{data.chip}</p>}
          <button
            type="button"
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            className="rounded-full border border-line px-3 py-1 text-ink disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>
      {weather.isPending && (
        <div className="h-32 animate-pulse rounded-xl bg-wash" aria-busy="true" aria-label="Loading weather" />
      )}
      {data?.state === "empty" && <p className="text-muted">Weather has not come in yet.</p>}
      {data?.state === "unknown" && (
        <p className="text-muted">Weather has not come in. This is not a forecast.</p>
      )}
      {data && (data.state === "ready" || data.state === "stale") && <Forecast data={data} />}
    </section>
  );
}

function Forecast({ data }: { data: WeatherForecast }) {
  return (
    <div>
      <p className="text-6xl font-semibold tabular-nums tracking-tight">{data.temp_f}°</p>
      <p className="mt-2 text-lg text-muted tabular-nums">
        H {data.high_f} L {data.low_f}
      </p>
      <p className="mt-3 text-xl">{data.summary}</p>
    </div>
  );
}
