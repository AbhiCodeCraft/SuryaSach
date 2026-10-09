import { orientationLabel } from "@/lib/system-profile";
import type { SystemWrite } from "@/types/system";

export function SystemSummary({ system }: { system: SystemWrite }) {
  const rows = [
    ["Capacity", `${system.capacity_kw} kW`],
    ["Location", system.location_label],
    ["Coordinates", `${system.latitude}, ${system.longitude}`],
    ["Installed", system.install_date ?? `${system.install_year} (year only)`],
    ["Orientation", orientationLabel(system.azimuth_degrees)],
    ["Panel tilt", system.tilt_degrees === null ? "Not known" : `${system.tilt_degrees}° from horizontal`],
    ["Installer", system.vendor_name || "Not provided"],
  ];
  return (
    <dl className="divide-y divide-emerald-950/10">
      {rows.map(([label, value]) => (
        <div key={label} className="grid gap-1 py-4 sm:grid-cols-[140px_1fr] sm:gap-4">
          <dt className="text-sm text-stone-600">{label}</dt>
          <dd className="break-words text-sm font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
