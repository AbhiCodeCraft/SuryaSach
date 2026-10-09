"use client";

import { useEffect, useState } from "react";
import { getSystem } from "@/lib/api";
import type { SolarSystem } from "@/types/system";
import { SystemSummary } from "@/components/system-summary";
import { SystemForm } from "@/components/system-form";

export function SystemDetail({ systemId }: { systemId: string }) {
  const [system, setSystem] = useState<SolarSystem | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    getSystem(systemId, controller.signal).then((data) => {
      if (!controller.signal.aborted) setSystem(data);
    }).catch((error: Error) => {
      if (!controller.signal.aborted) setError(error.message);
    });
    return () => controller.abort();
  }, [systemId, attempt]);

  if (error) return <div className="error-box" role="alert">{error}<button className="secondary-button mt-4 block" onClick={() => { setError(""); setAttempt((n) => n + 1); }}>Retry loading</button></div>;
  if (!system) return <p role="status">Loading your solar system…</p>;
  if (editing) return <SystemForm initial={system} onCancel={() => setEditing(false)} onSaved={(updated) => { setSystem(updated); setEditing(false); setSaved(true); }} />;
  return (
    <>
      <p className="eyebrow">My solar system</p>
      <h1 className="page-title">Your solar system is ready.</h1>
      <p className="mt-4 text-stone-600">Your profile is saved. Here’s what we know about your rooftop.</p>
      {saved && <p role="status" className="mt-4 font-medium">Changes saved.</p>}
      <section className="profile-card mt-8" aria-label="Saved system profile">
        <SystemSummary system={system} />
        <button className="secondary-button mt-6" onClick={() => { setSaved(false); setEditing(true); }}>Edit system</button>
      </section>
      <aside className="mt-8 border-l-2 border-amber-500 pl-5 text-sm leading-6 text-stone-600">
        <p className="font-semibold text-emerald-950">A profile is the first step.</p>
        <p>Generation readings and weather-adjusted performance verification are coming in later milestones. No performance assessment has been made yet.</p>
      </aside>
    </>
  );
}
