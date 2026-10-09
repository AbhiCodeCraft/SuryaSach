import Link from "next/link";

export default function SystemsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto min-h-dvh max-w-4xl px-5 sm:px-10">
      <header className="flex items-center justify-between border-b border-emerald-950/10 py-6">
        <Link href="/" className="text-lg font-bold">☀ Surya Sach</Link>
        <Link href="/systems" className="text-sm underline underline-offset-4">My systems</Link>
      </header>
      <main className="py-10 sm:py-14">{children}</main>
      <footer className="border-t border-emerald-950/10 py-6 text-xs leading-5 text-stone-600">
        Local preview · No sign-in yet. Profiles on this server are shared. Use test information only.
      </footer>
    </div>
  );
}
