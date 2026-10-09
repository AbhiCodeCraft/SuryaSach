import { expect, test } from "@playwright/test";

test("the home screen connects to the real backend", async ({ page }) => {
  const healthResponse = page.waitForResponse((response) =>
    new URL(response.url()).pathname === "/health" && response.request().method() === "GET",
  );
  await page.goto("/");
  const response = await healthResponse;
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ok", service: "surya-sach-api" });
  await expect(page.getByRole("status")).toHaveText("Backend: Connected");
  await expect(page.getByRole("heading", { name: "Surya Sach." })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("shows connecting while waiting for the backend", async ({ page }) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  await page.route("**/health", async (route) => {
    await gate;
    await route.continue();
  });
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Backend: Connecting...");
  release();
  await expect(page.getByRole("status")).toHaveText("Backend: Connected");
});

test("network failure is recoverable with Retry", async ({ page }) => {
  await page.route("**/health", (route) => route.abort("connectionrefused"));
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Backend: Unavailable");
  await page.unroute("**/health");
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("status")).toHaveText("Backend: Connected");
});

test("an invalid health response is not shown as connected", async ({ page }) => {
  await page.route("**/health", (route) => route.fulfill({
    json: { status: "ok", service: "different-service" },
  }));
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Backend: Unavailable");
});

test("a stalled backend times out", async ({ page }) => {
  await page.route("**/health", () => {});
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Backend: Unavailable", { timeout: 10000 });
});
