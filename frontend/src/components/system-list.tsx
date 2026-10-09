"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listSystems } from "@/lib/api";
import type { SolarSystem } from "@/types/system";

export function SystemList() {
  const [systems, setSystems] = useState<SolarSystem[] | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    listSystems(controller.signal).then((data) => {
      if (!controller.signal.aborted) setSystems(data);
    }).catch((error: Error) => {
      if (!controller.signal.aborted) setError(error.message);
    });
    return () => controller.abort();
  }, [attempt]);

  return (
    <>
      <p className="eyebrow">Your rooftop, on record</p>
      <h1 className="page-title">My solar systems</h1>
      <p className="mt-4 max-w-xl text-stone-600">Start with what you know. You can add or correct the details later.</p>
      <Link href="/systems/new" className="primary-button mt-7 inline-block">Add a solar system</Link>
      {error ? <div className="error-box mt-8" role="alert">{error}<button className="secondary-button mt-4 block" onClick={() => { setError(""); setAttempt((n) => n + 1); }}>Retry loading</button></div>
        : systems === null ? <p role="status" className="mt-8">Loading your systems…</p>
        : systems.length === 0 ? <div className="profile-card mt-8"><h2 className="text-xl font-semibold">A little context goes a long way.</h2><p className="mt-3 text-stone-600">No systems saved yet. Add your rooftop details to get ready for future performance checks.</p></div>
        : <ul className="mt-8 grid gap-4">{systems.map((system) => <li key={system.system_id}>
          <Link href={`/systems/${system.system_id}`} className="profile-card block hover:border-emerald-800">
            <h2 className="break-words text-xl font-semibold">{system.capacity_kw} kW · {system.location_label}</h2>
            <p className="mt-2 text-sm text-stone-600">Installed {system.install_date ?? `${system.install_year} (year only)`}</p>
            <span className="mt-5 inline-block text-sm font-semibold underline underline-offset-4">View system →</span>
          </Link>
        </li>)}</ul>}
    </>
  );
}
