import { test, expect } from "@playwright/test";
import { writeFixtureTickets, FIXTURE_TICKETS } from "./fixtures.js";

test.beforeEach(() => {
	writeFixtureTickets();
});

test.describe("Board rendering", () => {
	test("should render all six status columns", async ({ page }) => {
		await page.goto("/");
		const columns = page.locator("[data-testid^='column-']");
		await expect(columns).toHaveCount(6);
		await expect(page.locator("[data-testid='column-blocked']")).toBeVisible();
		await expect(page.locator("[data-testid='column-design-needed']")).toBeVisible();
		await expect(page.locator("[data-testid='column-plan-needed']")).toBeVisible();
		await expect(page.locator("[data-testid='column-ready']")).toBeVisible();
		await expect(page.locator("[data-testid='column-in-review']")).toBeVisible();
		await expect(page.locator("[data-testid='column-done']")).toBeVisible();
	});

	test("should display column labels and ticket counts", async ({ page }) => {
		await page.goto("/");
		const readyColumn = page.locator("[data-testid='column-ready']");
		await expect(readyColumn.locator("h2")).toHaveText("Ready");
		const readyTickets = FIXTURE_TICKETS.filter((t) => t.status === "ready");
		await expect(readyColumn.locator("h2 + span")).toHaveText(String(readyTickets.length));
	});

	test("should render ticket cards with ID and title", async ({ page }) => {
		await page.goto("/");
		const card = page.locator("[data-testid='card-T4']");
		await expect(card).toBeVisible();
		await expect(card).toContainText("T4");
		await expect(card).toContainText("Ready ticket alpha");
	});

	test("should display dependency badges on cards with dependencies", async ({ page }) => {
		await page.goto("/");
		const card = page.locator("[data-testid='card-T1']");
		await expect(card).toContainText("1 dep");
	});

	test("should sort tickets numerically within columns", async ({ page }) => {
		await page.goto("/");
		const readyColumn = page.locator("[data-testid='column-ready']");
		const cards = readyColumn.locator("[data-testid^='card-']");
		await expect(cards).toHaveCount(2);
		const firstId = await cards.nth(0).locator("[data-testid^='card-']").or(cards.nth(0)).getAttribute("data-testid");
		const secondId = await cards.nth(1).getAttribute("data-testid");
		expect(firstId).toBe("card-T4");
		expect(secondId).toBe("card-T5");
	});
});
