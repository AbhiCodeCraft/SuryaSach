import { expect, test, type Page } from "@playwright/test";

async function continueStep(page: Page) {
  await page.getByRole("button", { name: "Continue", exact: true }).click();
}

async function fillProfile(page: Page, location: string, known = false) {
  await page.getByLabel("Installed capacity (kW)", { exact: true }).fill("3.5");
  await continueStep(page);
  await page.getByLabel("City or location name").fill(location);
  await page.getByLabel("Latitude", { exact: true }).fill("28.6139");
  await page.getByLabel("Longitude", { exact: true }).fill("77.2090");
  await continueStep(page);
  if (known) await page.getByLabel("Installation date", { exact: true }).fill("2020-01-15");
  else {
    await page.getByLabel("I only know the year").check();
    await page.getByLabel("Installation year", { exact: true }).fill("2021");
  }
  await continueStep(page);
  await page.getByLabel(known ? "North" : "I don’t know", { exact: true }).check();
  await continueStep(page);
  await page.getByLabel(known ? "I know the angle" : "I don’t know", { exact: true }).check();
  if (known) await page.getByLabel("Tilt angle (degrees)", { exact: true }).fill("0");
  await continueStep(page);
  await page.getByRole("button", { name: "Review system" }).click();
}

test("create unknown profile, retrieve, edit, reload, and find in list", async ({ page }) => {
  const location = `Delhi test ${Date.now()}`;
  await page.goto("/systems/new");
  await fillProfile(page, location);
  await expect(page.getByRole("heading", { name: "Does everything look right?" })).toBeVisible();
  await expect(page.getByText("Not known", { exact: true })).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const createdResponse = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/systems");
  await page.getByRole("button", { name: "Save my system" }).click();
  const response = await createdResponse;
  expect(response.status()).toBe(201);
  const profile = await response.json();
  expect(profile.azimuth_degrees).toBeNull();
  expect(profile.tilt_degrees).toBeNull();
  expect(profile.install_date).toBeNull();
  expect(profile.install_year).toBe(2021);
  expect(profile.vendor_name).toBeNull();
  await expect(page.getByRole("heading", { name: "Your solar system is ready." })).toBeVisible();
  await expect(page.getByText(location, { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Edit system" }).click();
  await page.getByLabel("Installed capacity (kW)", { exact: true }).fill("4.2");
  await continueStep(page);
  await expect(page.getByLabel("City or location name")).toHaveValue(location);
  await continueStep(page);
  await expect(page.getByLabel("Installation year", { exact: true })).toHaveValue("2021");
  await continueStep(page);
  await page.getByLabel("I know the exact angle").check();
  await page.getByLabel("Azimuth in degrees", { exact: false }).fill("123.4");
  await continueStep(page);
  await page.getByLabel("I know the angle", { exact: true }).check();
  await page.getByLabel("Tilt angle (degrees)", { exact: true }).fill("0");
  await continueStep(page);
  await page.getByLabel("Installer name (optional)").fill("  Test installer  ");
  await page.getByRole("button", { name: "Review system" }).click();
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("status")).toHaveText("Changes saved.");
  await page.reload();
  await expect(page.getByText("4.2 kW", { exact: true })).toBeVisible();
  await expect(page.getByText("123.4° clockwise from true north", { exact: true })).toBeVisible();
  await expect(page.getByText("0° from horizontal", { exact: true })).toBeVisible();
  await expect(page.getByText("Test installer", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Edit system" }).click();
  for (let step = 0; step < 3; step++) await continueStep(page);
  await expect(page.getByLabel("I know the exact angle")).toBeChecked();
  await expect(page.getByLabel("Azimuth in degrees", { exact: false })).toHaveValue("123.4");
  await page.getByRole("button", { name: "Cancel editing" }).click();
  await page.getByRole("link", { name: "My systems", exact: true }).click();
  await expect(page.getByRole("heading", { name: `4.2 kW · ${location}` })).toBeVisible();
});

test("required values and unknown selections are validated without losing entries", async ({ page }) => {
  await page.goto("/systems/new");
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("capacity greater than 0");
  await page.getByLabel("Installed capacity (kW)", { exact: true }).fill("101");
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toBeVisible();
  await page.getByLabel("Installed capacity (kW)", { exact: true }).fill("3");
  await continueStep(page);
  await page.getByLabel("City or location name").fill("Jaipur");
  await page.getByLabel("Latitude", { exact: true }).fill("91");
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("latitude");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("longitude");
  await expect(page.getByLabel("City or location name")).toHaveValue("Jaipur");
  await page.getByLabel("Latitude", { exact: true }).fill("26.9");
  await page.getByLabel("Longitude", { exact: true }).fill("75.8");
  await continueStep(page);
  await page.getByLabel("Installation date", { exact: true }).fill("2099-01-01");
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("installation date");
  await page.getByLabel("Installation date", { exact: true }).fill("2020-02-01");
  await continueStep(page);
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Choose a direction");
  await page.getByLabel("I don’t know", { exact: true }).check();
  await continueStep(page);
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("Choose whether");
  await page.getByLabel("I know the angle", { exact: true }).check();
  await page.getByLabel("Tilt angle (degrees)", { exact: true }).fill("91");
  await continueStep(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText("between 0 and 90");
});

test("backend error keeps review and permits a successful retry with zero-degree angles", async ({ page }) => {
  const location = `Known test ${Date.now()}`;
  await page.goto("/systems/new");
  await fillProfile(page, location, true);
  await page.route("**/systems", (route) => route.request().method() === "POST"
    ? route.fulfill({ status: 503, json: { detail: "Unavailable" } }) : route.continue());
  await page.getByRole("button", { name: "Save my system" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("temporarily unavailable");
  await expect(page.getByText(location, { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Does everything look right?" })).toBeVisible();
  await page.unroute("**/systems");
  await page.getByRole("button", { name: "Save my system" }).click();
  await expect(page.getByRole("heading", { name: "Your solar system is ready." })).toBeVisible();
  await expect(page.getByText("North (0°)", { exact: true })).toBeVisible();
  await expect(page.getByText("0° from horizontal", { exact: true })).toBeVisible();
  await expect(page.getByText("2020-01-15", { exact: true })).toBeVisible();
});

test("missing profile and failed list render useful errors", async ({ page }) => {
  await page.goto("/systems/00000000-0000-0000-0000-000000000000");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("could not be found");
  await page.route("**/systems", (route) => route.request().resourceType() === "fetch"
    ? route.abort("connectionrefused") : route.continue());
  await page.goto("/systems");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("couldn’t reach");
  await page.unroute("**/systems");
  await page.getByRole("button", { name: "Retry loading" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("main").getByRole("status")).toHaveCount(0);
});
