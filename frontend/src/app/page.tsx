import { BackendStatus } from "@/components/backend-status";
import Link from "next/link";

export default function Home() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-6xl flex-col px-6 sm:px-12">
      <header className="flex items-center justify-between border-b border-emerald-950/10 py-7">
        <Link href="/" aria-label="Surya Sach home" className="flex items-center gap-3 rounded text-lg font-bold tracking-tight focus-visible:outline-2 focus-visible:outline-offset-4">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <circle cx="16" cy="16" r="7" fill="#eebd4c" />
            <path d="M16 2v4m0 20v4M2 16h4m20 0h4M6 6l3 3m14 14 3 3M6 26l3-3M23 9l3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          Surya Sach
        </Link>
        <span className="rounded-full border border-emerald-950/15 px-3 py-1.5 text-[11px] font-medium uppercase tracking-widest">In development</span>
      </header>

      <main className="flex flex-1 flex-col justify-center py-16 sm:py-24">
        <div className="grid items-center gap-12 md:grid-cols-[1.3fr_0.7fr]">
          <section>
            <p className="mb-6 text-xs font-bold uppercase tracking-[0.2em] text-emerald-800">A clearer picture of your solar</p>
            <h1 className="text-5xl font-semibold tracking-tight sm:text-7xl">Surya Sach<span className="text-amber-600">.</span></h1>
            <h2 className="mt-6 max-w-xl text-xl leading-relaxed sm:text-2xl">Independent Rooftop Solar Performance Verification</h2>
            <p className="mt-5 max-w-lg text-base leading-7 text-stone-600">Know what your solar system produced — and what it reasonably should have.</p>
            <div className="mt-7 flex flex-wrap items-center gap-5">
              <Link href="/systems/new" className="primary-button">Add your solar system</Link>
              <Link href="/systems" className="text-sm font-semibold underline underline-offset-4">My systems →</Link>
            </div>
            <div className="mt-10 max-w-lg border-l-2 border-amber-500 pl-5">
              <p className="text-sm font-semibold">Built around evidence. Grounded in context.</p>
              <p className="mt-2 text-sm leading-6 text-stone-600">We’re building an independent way to understand rooftop solar performance, with weather-adjusted expectations and transparent assumptions.</p>
            </div>
          </section>

          <div className="relative mx-auto flex aspect-square w-full max-w-xs items-center justify-center rounded-full bg-[#efeee3]" aria-hidden="true">
            <svg viewBox="0 0 320 320" className="w-full">
              <circle cx="214" cy="95" r="32" fill="#eebd4c" />
              <circle cx="214" cy="95" r="46" fill="none" stroke="#eebd4c" strokeDasharray="2 10" strokeWidth="2" />
              <path d="M51 230h220M94 230v-59l65-49 66 49v59" fill="#f8f7f2" stroke="#244c40" strokeWidth="3" strokeLinejoin="round" />
              <path d="m66 177 93-69 94 69" fill="none" stroke="#244c40" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
              <path d="m101 176 45-39h49l43 39z" fill="#244c40" stroke="#f8f7f2" strokeWidth="2" />
              <path d="m124 176 34-39m-9 39 20-39m6 39 5-39m20 39-9-39m-76 19h99" stroke="#a9c4b1" strokeWidth="1.5" />
              <path d="M149 230v-33h25v33" fill="#d9e1d2" stroke="#244c40" strokeWidth="2" />
            </svg>
          </div>
        </div>
        <p className="mt-14 text-xs leading-5 text-stone-500">Early preview · Performance checks and reports are not available yet.</p>
      </main>

      <footer className="flex flex-wrap items-center justify-between gap-4 border-t border-emerald-950/10 py-6">
        <p className="text-xs text-stone-500">Made for Indian rooftops.</p>
        <BackendStatus />
      </footer>
    </div>
  );
}
