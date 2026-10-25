import { useQuery } from "@tanstack/react-query";
import { api, type CarMaintenance, type HouseholdCar } from "../api";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatStoredDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) {
    return iso;
  }
  const month = MONTHS[Number(match[2]) - 1];
  if (!month) {
    return iso;
  }
  return `${month} ${Number(match[3])}, ${match[1]}`;
}

export function CarsPage() {
  const cars = useQuery({ queryKey: ["cars"], queryFn: api.cars });
  const rows = cars.data?.cars;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Cars</h2>
        <a href="/api/cars/export" className="text-sm text-accent underline-offset-4 hover:underline">
          Export records
        </a>
      </div>
      {cars.isPending && (
        <div className="grid gap-6 lg:grid-cols-2" aria-busy="true" aria-label="Loading cars">
          <div className="h-40 animate-pulse rounded-2xl bg-wash" />
          <div className="h-40 animate-pulse rounded-2xl bg-wash" />
        </div>
      )}
      {cars.isError && <p className="text-muted">Cars have not come in. This is not an empty garage.</p>}
      {rows && rows.length === 0 && (
        <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
          <p className="text-muted">No cars yet. A nickname or a service date can be sent in chat.</p>
        </section>
      )}
      {rows && rows.length > 0 && (
        <div className={rows.length > 1 ? "grid gap-6 lg:grid-cols-2" : "grid gap-6"}>
          {rows.map((car) => (
            <CarCard key={car.id} car={car} />
          ))}
        </div>
      )}
    </div>
  );
}

function CarCard({ car }: { car: HouseholdCar }) {
  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <h3 className="text-xl font-semibold tracking-tight">{car.nickname ?? "Unnamed car"}</h3>
      {car.maintenance.length === 0 ? (
        <p className="mt-3 text-muted">No maintenance recorded yet.</p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {car.maintenance.map((event) => (
            <MaintenanceRow key={event.id} event={event} />
          ))}
        </ul>
      )}
      {car.missing.length > 0 && (
        <ul className="mt-4 space-y-1 text-sm text-muted">
          {car.missing.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function MaintenanceRow({ event }: { event: CarMaintenance }) {
  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <p className="text-lg">{event.kind_label}</p>
      <p className="text-sm text-muted tabular-nums">
        {event.performed_on ? formatStoredDate(event.performed_on) : "Date not recorded"}
      </p>
      {event.evidence_note && <p className="mt-1 text-sm">{event.evidence_note}</p>}
      {event.next_due && (
        <p className="mt-1 text-sm text-muted tabular-nums">Next due {formatStoredDate(event.next_due)}</p>
      )}
    </li>
  );
}
