import { useQuery } from "@tanstack/react-query";
import { api, type HouseholdDog, type VetRecord } from "../api";

const KIND_LABEL: Record<string, string> = {
  vaccine: "Vaccine",
  vet_visit: "Vet visit",
  payment: "Payment",
  service: "Service",
  registration: "Registration",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function DogsPage() {
  const dogs = useQuery({ queryKey: ["dogs"], queryFn: api.dogs });
  const page = dogs.data;

  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-[0_16px_40px_-28px_var(--shadow)]">
      <h2 className="mb-3 text-2xl">Dogs</h2>
      {dogs.isPending && (
        <div className="space-y-3" aria-busy="true" aria-label="Loading the dogs">
          <div className="h-20 animate-pulse rounded-xl bg-wash" />
          <div className="h-20 animate-pulse rounded-xl bg-wash" />
        </div>
      )}
      {dogs.isError && (
        <p className="text-muted">Dog records have not come in. This is not an empty list.</p>
      )}
      {page && (
        <div className="divide-y divide-line">
          {page.dogs.map((dog) => (
            <DogCard key={dog.id} dog={dog} />
          ))}
        </div>
      )}
    </section>
  );
}

function DogCard({ dog }: { dog: HouseholdDog }) {
  return (
    <article className="py-4 first:pt-0 last:pb-0">
      <h3 className="text-xl">{dog.name}</h3>
      {dog.ask && <p className="mt-2 text-muted">{dog.ask}</p>}
      {dog.records.length === 0 ? (
        <p className="mt-2 text-muted">No vet records stored.</p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {dog.records.map((record) => (
            <VetRow key={record.id} record={record} />
          ))}
        </ul>
      )}
    </article>
  );
}

function VetRow({ record }: { record: VetRecord }) {
  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <p className="text-lg">
        {KIND_LABEL[record.kind] ?? record.kind}
        {" · "}
        <span className="tabular-nums">{record.date ? formatStoredDate(record.date) : "Date not stored"}</span>
      </p>
      {record.evidence_note && <p className="text-sm text-muted">{record.evidence_note}</p>}
      {record.next_due && (
        <p className="text-sm text-muted tabular-nums">Next due {formatStoredDate(record.next_due)}</p>
      )}
    </li>
  );
}

function formatStoredDate(iso: string): string {
  const [year, month, day] = iso.split("-");
  const monthIndex = Number(month) - 1;
  const label = MONTHS[monthIndex];
  if (!year || !label || !day) {
    return iso;
  }
  return `${label} ${Number(day)}, ${year}`;
}
