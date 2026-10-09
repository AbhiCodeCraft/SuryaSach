import type { HealthResponse } from "@/types/api";
import type { SolarSystem, SystemWrite } from "@/types/system";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const timeout = AbortSignal.timeout(5000);
  const response = await fetch(`${API_BASE_URL}/health`, {
    cache: "no-store",
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });

  if (!response.ok) throw new Error("Backend health check failed");

  const data: unknown = await response.json();
  if (
    typeof data !== "object" || data === null ||
    !("status" in data) || data.status !== "ok" ||
    !("service" in data) || data.service !== "surya-sach-api"
  ) {
    throw new Error("Unexpected backend health response");
  }
  return data as HealthResponse;
}

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

async function request(path: string, method = "GET", body?: SystemWrite, signal?: AbortSignal): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      cache: "no-store",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(5000)]) : AbortSignal.timeout(5000),
    });
  } catch {
    throw new ApiError(method === "GET"
      ? "We couldn’t reach your solar profiles. Check that the backend is running and try again."
      : "We couldn’t confirm the save. Your entries are still here. Check My systems before retrying to avoid a duplicate.");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 404) throw new ApiError("This solar system could not be found.", 404);
    if (response.status === 422 && Array.isArray(data?.detail)) {
      const messages = data.detail.map((item: { loc?: string[]; msg?: string }) =>
        `${item.loc?.slice(1).join(" ").replaceAll("_", " ") || "Profile"}: ${item.msg || "Invalid value"}`,
      );
      throw new ApiError(messages.join(". "), 422);
    }
    throw new ApiError("Your profiles are temporarily unavailable. Please try again shortly.", response.status);
  }
  return data;
}

function parseSystem(value: unknown): SolarSystem {
  if (!value || typeof value !== "object") throw new ApiError("The backend returned an unexpected profile.");
  const data = value as Record<string, unknown>;
  const strings = ["system_id", "owner_id", "location_label", "created_at", "updated_at"];
  const numbers = ["capacity_kw", "latitude", "longitude"];
  const nullableNumbers = ["install_year", "azimuth_degrees", "tilt_degrees"];
  if (strings.some((key) => typeof data[key] !== "string") ||
      numbers.some((key) => typeof data[key] !== "number" || !Number.isFinite(data[key])) ||
      nullableNumbers.some((key) => data[key] !== null && (typeof data[key] !== "number" || !Number.isFinite(data[key]))) ||
      ["vendor_name", "install_date"].some((key) => data[key] !== null && typeof data[key] !== "string")) {
    throw new ApiError("The backend returned an unexpected profile.");
  }
  return data as unknown as SolarSystem;
}

export async function listSystems(signal?: AbortSignal): Promise<SolarSystem[]> {
  const data = await request("/systems", "GET", undefined, signal);
  if (!Array.isArray(data)) throw new ApiError("The backend returned an unexpected profile list.");
  return data.map(parseSystem);
}

export async function getSystem(id: string, signal?: AbortSignal): Promise<SolarSystem> {
  return parseSystem(await request(`/systems/${encodeURIComponent(id)}`, "GET", undefined, signal));
}

export async function saveSystem(profile: SystemWrite, id?: string): Promise<SolarSystem> {
  return parseSystem(await request(id ? `/systems/${encodeURIComponent(id)}` : "/systems", id ? "PUT" : "POST", profile));
}
