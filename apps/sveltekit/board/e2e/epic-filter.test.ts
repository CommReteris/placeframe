import { test, expect } from "@playwright/test";
import { writeFixtureTickets } from "./fixtures.js";

test.beforeEach(() => {
	writeFixtureTickets();
});

test.describe("Epic chips", () => {
	test("should show epic chips on cards with epics", async ({ page }) => {
		await page.goto("/");
		await expect(page.locator("[data-testid='epic-chip-ci']")).toBeVisible();
		await expect(page.locator("[data-testid='epic-chip-board']")).toBeVisible();
	});

	test("should not show epic chips on root-level cards", async ({ page }) => {
		await page.goto("/");
		const card = page.locator("[data-testid='card-T4']");
		await expect(card).toBeVisible();
		await expect(card.locator("[data-testid^='epic-chip-']")).toHaveCount(0);
	});
});

test.describe("Epic filtering", () => {
	test("should filter to show only tickets from selected epic", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const filter = page.locator("[data-testid='epic-filter']");
		await filter.selectOption("ci");
		await expect(page.locator("[data-testid='card-T7']")).toBeVisible();
		await expect(page.locator("[data-testid='card-T4']")).not.toBeVisible();
		await expect(page.locator("[data-testid='card-T5']")).not.toBeVisible();
		await expect(page.locator("[data-testid='card-T1']")).not.toBeVisible();
	});

	test("should show all tickets when All epics is selected", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const filter = page.locator("[data-testid='epic-filter']");
		await filter.selectOption("ci");
		await expect(page.locator("[data-testid='card-T4']")).not.toBeVisible();
		await filter.selectOption("");
		await expect(page.locator("[data-testid='card-T4']")).toBeVisible();
		await expect(page.locator("[data-testid='card-T7']")).toBeVisible();
	});

	test("should persist epic filter in URL query param", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const filter = page.locator("[data-testid='epic-filter']");
		await filter.selectOption("ci");
		await expect(page).toHaveURL(/epic=ci/);
	});

	test("should apply epic filter from URL on page load", async ({ page }) => {
		await page.goto("/?epic=ci");
		await expect(page.locator("[data-testid='card-T7']")).toBeVisible();
		await expect(page.locator("[data-testid='card-T4']")).not.toBeVisible();
		const filter = page.locator("[data-testid='epic-filter']");
		await expect(filter).toHaveValue("ci");
	});
});

test.describe("Epic sections", () => {
	test("should show collapsible epic sections within columns", async ({ page }) => {
		await page.goto("/");
		const readyColumn = page.locator("[data-testid='column-ready']");
		await expect(readyColumn.locator("[data-testid='epic-section-ci']")).toBeVisible();
		await expect(readyColumn.locator("[data-testid='epic-section-ungrouped']")).toBeVisible();
	});

	test("should collapse and expand epic sections", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const readyColumn = page.locator("[data-testid='column-ready']");
		await expect(readyColumn.locator("[data-testid='card-T7']")).toBeVisible();
		await readyColumn.locator("[data-testid='epic-section-ci']").click();
		await expect(readyColumn.locator("[data-testid='card-T7']")).not.toBeVisible();
		await readyColumn.locator("[data-testid='epic-section-ci']").click();
		await expect(readyColumn.locator("[data-testid='card-T7']")).toBeVisible();
	});

	test("should not show epic section headers when column has only ungrouped tickets", async ({ page }) => {
		await page.goto("/");
		const designColumn = page.locator("[data-testid='column-design-needed']");
		await expect(designColumn.locator("[data-testid^='epic-section-']")).toHaveCount(0);
	});
});
