import { test, expect } from "@playwright/test";
import { writeFixtureTickets } from "./fixtures.js";

test.beforeEach(() => {
	writeFixtureTickets();
});

test.describe("Detail panel", () => {
	test("should open when a card is clicked", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		await expect(page.locator("aside")).toBeVisible();
		await expect(page.locator("aside")).toContainText("T4");
		await expect(page.locator("aside")).toContainText("Ready ticket alpha");
	});

	test("should close when the close button is clicked", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		await expect(page.locator("aside")).toBeVisible();
		await page.getByLabel("Close detail panel").click();
		await expect(page.locator("aside")).not.toBeVisible();
	});

	test("should close when the backdrop is clicked", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		await expect(page.locator("aside")).toBeVisible();
		await page.locator(".bg-black\\/50").click({ position: { x: 10, y: 10 } });
		await expect(page.locator("aside")).not.toBeVisible();
	});

	test("should close when Escape is pressed", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		await expect(page.locator("aside")).toBeVisible();
		await page.keyboard.press("Escape");
		await expect(page.locator("aside")).not.toBeVisible();
	});

	test("should display ticket status and dependencies", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T1']").click();
		await expect(page.locator("aside")).toContainText("Blocked");
		await expect(page.locator("aside")).toContainText("T3");
	});

	test("should render markdown content in the body", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		const body = page.locator("aside .prose");
		await expect(body.locator("ul")).toBeVisible();
		await expect(body.locator("li")).toHaveCount(2);
		await expect(body.locator("strong")).toContainText("Bold text");
		await expect(body.locator("em")).toContainText("italic text");
	});

	test("should resize when the drag handle is dragged", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		await page.locator("[data-testid='card-T4']").click();
		const aside = page.locator("aside");
		await expect(aside).toBeVisible();
		// Wait for the fly transition to complete (300ms)
		await page.waitForTimeout(400);
		const initialWidth = await aside.evaluate((element) => element.getBoundingClientRect().width);
		const handle = page.locator(".cursor-col-resize");
		const handleBox = await handle.boundingBox();
		if (!handleBox) throw new Error("Handle not found");
		const startX = handleBox.x + handleBox.width / 2;
		const centerY = handleBox.y + handleBox.height / 2;
		// Use dispatchEvent for pointer events (page.mouse doesn't trigger setPointerCapture correctly)
		await handle.dispatchEvent("pointerdown", { clientX: startX, clientY: centerY, pointerId: 1 });
		await handle.dispatchEvent("pointermove", { clientX: startX - 100, clientY: centerY, pointerId: 1 });
		await handle.dispatchEvent("pointerup", { pointerId: 1 });
		const newWidth = await aside.evaluate((element) => element.getBoundingClientRect().width);
		expect(newWidth).toBeGreaterThan(initialWidth);
	});
});

test.describe("Search", () => {
	test("should filter cards by title", async ({ page }) => {
		await page.goto("/");
		const searchInput = page.getByPlaceholder("Search tickets...");
		await searchInput.fill("alpha");
		await expect(page.locator("[data-testid='card-T4']")).toBeVisible();
		await expect(page.locator("[data-testid='card-T5']")).not.toBeVisible();
		await expect(page.locator("[data-testid='card-T1']")).not.toBeVisible();
	});

	test("should filter cards by ticket ID", async ({ page }) => {
		await page.goto("/");
		const searchInput = page.getByPlaceholder("Search tickets...");
		await searchInput.fill("T6");
		await expect(page.locator("[data-testid='card-T6']")).toBeVisible();
		await expect(page.locator("[data-testid='card-T4']")).not.toBeVisible();
	});

	test("should show empty columns when search has no matches", async ({ page }) => {
		await page.goto("/");
		const searchInput = page.getByPlaceholder("Search tickets...");
		await searchInput.fill("nonexistent query");
		const cards = page.locator("[data-testid^='card-']");
		await expect(cards).toHaveCount(0);
	});
});
