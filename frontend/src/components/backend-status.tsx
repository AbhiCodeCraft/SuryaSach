"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

type Status = "Connecting..." | "Connected" | "Unavailable";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("Connecting...");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then(() => {
        if (!controller.signal.aborted) setStatus("Connected");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("Unavailable");
      });
    return () => controller.abort();
  }, [attempt]);

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-stone-600">
      <span role="status" className="flex items-center gap-2">
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${status === "Connected" ? "bg-emerald-600" : status === "Unavailable" ? "bg-amber-600" : "bg-stone-400"}`} />
        Backend: {status}
      </span>
      {status === "Unavailable" && (
        <button
          type="button"
          className="rounded px-2 py-1 font-medium text-emerald-900 underline underline-offset-4 hover:bg-emerald-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
          onClick={() => { setStatus("Connecting..."); setAttempt((value) => value + 1); }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
