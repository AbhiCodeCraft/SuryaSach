"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { saveSystem } from "@/lib/api";
import { orientations, todayInIndia } from "@/lib/system-profile";
import { SystemSummary } from "@/components/system-summary";
import type { SolarSystem, SystemWrite } from "@/types/system";

interface Draft {
  capacity: string; location: string; latitude: string; longitude: string;
  installationMode: string; installDate: string; installYear: string;
  orientation: string; exactAzimuth: string;
  tiltMode: string; tilt: string; vendor: string;
}
type Errors = Partial<Record<keyof Draft, string>>;

function initialDraft(system?: SolarSystem): Draft {
  return {
    capacity: system ? String(system.capacity_kw) : "",
    location: system?.location_label ?? "",
    latitude: system ? String(system.latitude) : "",
    longitude: system ? String(system.longitude) : "",
    installationMode: system?.install_year ? "year" : "date",
    installDate: system?.install_date ?? "",
    installYear: system?.install_year ? String(system.install_year) : "",
    orientation: !system ? "" : system.azimuth_degrees === null ? "unknown"
      : orientations.some((item) => Number(item.value) === system.azimuth_degrees) ? String(system.azimuth_degrees) : "exact",
    exactAzimuth: system?.azimuth_degrees == null ? "" : String(system.azimuth_degrees),
    tiltMode: !system ? "" : system.tilt_degrees === null ? "unknown" : "known",
    tilt: system?.tilt_degrees == null ? "" : String(system.tilt_degrees),
    vendor: system?.vendor_name ?? "",
  };
}

function profileFromDraft(draft: Draft): SystemWrite {
  return {
    capacity_kw: Number(draft.capacity), location_label: draft.location.trim(),
    latitude: Number(draft.latitude), longitude: Number(draft.longitude),
    install_date: draft.installationMode === "date" ? draft.installDate : null,
    install_year: draft.installationMode === "year" ? Number(draft.installYear) : null,
    azimuth_degrees: draft.orientation === "unknown" ? null : Number(draft.orientation === "exact" ? draft.exactAzimuth : draft.orientation),
    tilt_degrees: draft.tiltMode === "unknown" ? null : Number(draft.tilt),
    vendor_name: draft.vendor.trim() || null,
  };
}

function validate(draft: Draft, step: number): Errors {
  const errors: Errors = {};
  const numberInRange = (value: string, low: number, high: number) => value.trim() !== "" && Number.isFinite(Number(value)) && Number(value) >= low && Number(value) <= high;
  if (step === 0 && (!numberInRange(draft.capacity, 0, 100) || Number(draft.capacity) === 0)) errors.capacity = "Enter a capacity greater than 0 and up to 100 kW.";
  if (step === 1) {
    if (!draft.location.trim() || draft.location.trim().length > 120) errors.location = "Enter a location name of 1–120 characters.";
    if (!numberInRange(draft.latitude, -90, 90)) errors.latitude = "Enter a latitude between −90 and 90.";
    if (!numberInRange(draft.longitude, -180, 180)) errors.longitude = "Enter a longitude between −180 and 180.";
  }
  if (step === 2) {
    if (draft.installationMode === "date") {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(draft.installDate) || draft.installDate < "1900-01-01" || draft.installDate > todayInIndia()) errors.installDate = "Enter an installation date from 1900 through today in India.";
    } else if (!numberInRange(draft.installYear, 1900, Number(todayInIndia().slice(0, 4))) || !Number.isInteger(Number(draft.installYear))) errors.installYear = "Enter an installation year from 1900 through the current year.";
  }
  if (step === 3) {
    if (!draft.orientation) errors.orientation = "Choose a direction or select “I don’t know”.";
    if (draft.orientation === "exact" && (!numberInRange(draft.exactAzimuth, 0, 360) || Number(draft.exactAzimuth) === 360)) errors.exactAzimuth = "Enter an angle from 0 up to, but not including, 360°.";
  }
  if (step === 4) {
    if (!draft.tiltMode) errors.tiltMode = "Choose whether you know the tilt, or select “I don’t know”.";
    if (draft.tiltMode === "known" && !numberInRange(draft.tilt, 0, 90)) errors.tilt = "Enter a tilt between 0 and 90°.";
  }
  if (step === 5 && draft.vendor.trim().length > 120) errors.vendor = "Keep the installer name within 120 characters.";
  return errors;
}

const steps = [
  ["Your system", "Tell us about your rooftop solar system.", "Find the installed panel capacity on your invoice or system paperwork. Use kW, not daily generation in kWh."],
  ["Location", "Where is your system installed?", "Coordinates will let us use local solar and weather data in a later milestone."],
  ["Installation", "When was it installed?", "A year is enough if you don’t remember the exact date."],
  ["Orientation", "Which direction do the panels face?", "Choose the direction the front of your panels faces. If you’re unsure, it’s fine to say so."],
  ["Tilt", "Do you know the panel tilt?", "Tilt is the angle from horizontal: 0° is flat and 90° is vertical. There’s no need to guess."],
  ["Installer", "Who installed the system?", "This is optional. It simply stays with your system profile."],
  ["Review", "Does everything look right?", "Review what you’ve entered. Unknown details will stay unknown until you update them."],
];

export function SystemForm({ initial, onSaved, onCancel }: {
  initial?: SolarSystem; onSaved?: (system: SolarSystem) => void; onCancel?: () => void;
}) {
  const router = useRouter();
  const [draft, setDraft] = useState(() => initialDraft(initial));
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState<Errors>({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const errorBox = useRef<HTMLDivElement>(null);
  useEffect(() => { heading.current?.focus(); }, [step]);
  useEffect(() => { if (Object.keys(errors).length || saveError) errorBox.current?.focus(); }, [errors, saveError]);

  function update(key: keyof Draft, value: string) {
    setDraft((previous) => ({ ...previous, [key]: value }));
    setSaveError("");
  }

  function field(key: keyof Draft, label: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}) {
    return <div>
      <label htmlFor={key} className="text-sm font-semibold">{label}</label>
      <input id={key} name={key} className="field-input" value={draft[key]} onChange={(event) => update(key, event.target.value)} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `${key}-error` : undefined} {...props} />
      {errors[key] && <p id={`${key}-error`} className="mt-2 text-sm text-red-800">{errors[key]}</p>}
    </div>;
  }

  function choice(key: keyof Draft, value: string, label: string) {
    return <label key={value} className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm ${draft[key] === value ? "border-emerald-800 bg-emerald-50" : "border-stone-300 bg-white hover:border-emerald-700"}`}>
      <input type="radio" name={key} value={value} checked={draft[key] === value} onChange={() => update(key, value)} className="h-4 w-4 accent-emerald-800" />
      {label}
    </label>;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (saving) return;
    const currentErrors = validate(draft, step);
    if (Object.keys(currentErrors).length) { setErrors(currentErrors); return; }
    if (step < 6) { setErrors({}); setStep(step + 1); return; }
    for (let index = 0; index < 6; index++) {
      const found = validate(draft, index);
      if (Object.keys(found).length) { setStep(index); setErrors(found); return; }
    }
    setSaving(true);
    setSaveError("");
    try {
      const system = await saveSystem(profileFromDraft(draft), initial?.system_id);
      if (onSaved) onSaved(system);
      else router.push(`/systems/${system.system_id}`);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "We couldn’t save your system. Please try again.");
    } finally { setSaving(false); }
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-semibold text-emerald-800">
        <span className="uppercase tracking-widest">{initial ? "Edit your rooftop" : "Let’s get to know your rooftop"}</span>
        <span>Step {step + 1} of 7 · {steps[step][0]}</span>
      </div>
      <progress className="mt-4 h-1.5 w-full accent-emerald-800" value={step + 1} max={7} aria-label="Onboarding progress" />
      <h1 ref={heading} tabIndex={-1} className="page-title mt-8 focus:outline-none">{steps[step][1]}</h1>
      <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600">{steps[step][2]}</p>

      <form noValidate onSubmit={submit} className="profile-card mt-8" aria-busy={saving}>
        {(Object.values(errors).some(Boolean) || saveError) && <div ref={errorBox} tabIndex={-1} role="alert" className="error-box mb-6">
          {saveError || <><p className="font-semibold">Please check these details:</p><ul className="list-disc pl-5">{Object.entries(errors).filter(([, value]) => value).map(([key, value]) => <li key={key}>{value}</li>)}</ul></>}
          {saveError && <Link href="/systems" className="mt-2 block underline">Check My systems</Link>}
        </div>}

        {step === 0 && field("capacity", "Installed capacity (kW)", { type: "number", inputMode: "decimal", min: 0, max: 100, step: "any", required: true, placeholder: "For example, 3" })}
        {step === 1 && <div className="space-y-6">
          {field("location", "City or location name", { maxLength: 120, required: true, placeholder: "For example, Jaipur, Rajasthan" })}
          <div className="grid gap-6 sm:grid-cols-2">
            {field("latitude", "Latitude", { type: "number", inputMode: "decimal", min: -90, max: 90, step: "any", required: true })}
            {field("longitude", "Longitude", { type: "number", inputMode: "decimal", min: -180, max: 180, step: "any", required: true })}
          </div>
          <details className="text-sm leading-6 text-stone-600"><summary className="cursor-pointer font-semibold text-emerald-900">How do I find my coordinates?</summary><p className="mt-2">In your preferred map app, place a pin on the rooftop and copy its coordinates. The first number is latitude, the second is longitude. Enter decimal degrees. We don’t look up or verify the location name automatically.</p></details>
        </div>}
        {step === 2 && <div className="space-y-6">
          <fieldset><legend className="mb-3 text-sm font-semibold">How precisely do you remember?</legend><div className="grid gap-3 sm:grid-cols-2">{choice("installationMode", "date", "I know the date")}{choice("installationMode", "year", "I only know the year")}</div></fieldset>
          {draft.installationMode === "date" ? field("installDate", "Installation date", { type: "date", min: "1900-01-01", max: todayInIndia(), required: true }) : field("installYear", "Installation year", { type: "number", inputMode: "numeric", min: 1900, max: Number(todayInIndia().slice(0, 4)), step: 1, required: true, placeholder: "For example, 2022" })}
        </div>}
        {step === 3 && <div className="space-y-6">
          <fieldset><legend className="mb-3 text-sm font-semibold">Panel direction</legend><div className="grid gap-3 sm:grid-cols-2">{orientations.map((item) => choice("orientation", item.value, item.label))}{choice("orientation", "exact", "I know the exact angle")}{choice("orientation", "unknown", "I don’t know")}</div></fieldset>
          {draft.orientation === "exact" && field("exactAzimuth", "Azimuth in degrees (clockwise from true north)", { type: "number", min: 0, max: 359.999, step: "any", inputMode: "decimal", required: true })}
          <p className="text-sm leading-6 text-stone-600">North is 0°, East 90°, South 180°, West 270°. A compass direction is a user-reported approximation, not a measured roof survey.</p>
        </div>}
        {step === 4 && <div className="space-y-6">
          <fieldset><legend className="mb-3 text-sm font-semibold">Panel tilt</legend><div className="grid gap-3 sm:grid-cols-2">{choice("tiltMode", "known", "I know the angle")}{choice("tiltMode", "unknown", "I don’t know")}</div></fieldset>
          {draft.tiltMode === "known" && field("tilt", "Tilt angle (degrees)", { type: "number", min: 0, max: 90, step: "any", inputMode: "decimal", required: true })}
          {draft.tiltMode === "unknown" && <p className="text-sm leading-6 text-stone-600">That’s okay. We’ll save this as unknown, without substituting an angle.</p>}
        </div>}
        {step === 5 && field("vendor", "Installer name (optional)", { maxLength: 120, autoComplete: "organization", placeholder: "Leave blank if you prefer" })}
        {step === 6 && <><SystemSummary system={profileFromDraft(draft)} /><p className="mt-5 text-sm leading-6 text-stone-600">These are your reported details. Saving this profile does not assess system performance.</p></>}

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-emerald-950/10 pt-6">
          {step > 0 ? <button type="button" className="secondary-button" disabled={saving} onClick={() => { setStep(step - 1); setErrors({}); setSaveError(""); }}>Back</button> : <span />}
          <button type="submit" className="primary-button" disabled={saving}>{saving ? "Saving…" : step === 6 ? initial ? "Save changes" : "Save my system" : step === 5 ? "Review system" : "Continue"}</button>
        </div>
        {onCancel && <button type="button" className="mt-5 text-sm underline underline-offset-4" disabled={saving} onClick={onCancel}>Cancel editing</button>}
      </form>
    </>
  );
}
