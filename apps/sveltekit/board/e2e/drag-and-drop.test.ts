import { test, expect, type Page, type Locator } from "@playwright/test";
import { writeFixtureTickets } from "./fixtures.js";

test.beforeEach(() => {
	writeFixtureTickets();
});

async function dragCardToColumn(page: Page, card: Locator, target: Locator): Promise<void> {
	await page.evaluate(
		async ([sourceSelector, targetSelector]) => {
			const source = document.querySelector(sourceSelector!);
			const targetElement = document.querySelector(targetSelector!);
			if (!source || !targetElement) throw new Error("Source or target not found");

			const dataTransfer = new DataTransfer();
			source.dispatchEvent(new DragEvent("dragstart", { bubbles: true, dataTransfer }));
			targetElement.dispatchEvent(new DragEvent("dragover", { bubbles: true, dataTransfer }));
			targetElement.dispatchEvent(new DragEvent("drop", { bubbles: true, dataTransfer }));
			source.dispatchEvent(new DragEvent("dragend", { bubbles: true, dataTransfer }));
		},
		[
			await card.evaluate((element) => {
				const testId = element.getAttribute("data-testid");
				return `[data-testid='${testId}']`;
			}),
			await target.evaluate((element) => {
				const role = element.getAttribute("role");
				const parent = element.closest("[data-testid]");
				const parentTestId = parent?.getAttribute("data-testid");
				return `[data-testid='${parentTestId}'] [role='${role}']`;
			}),
		],
	);
}

test.describe("Drag and drop", () => {
	test("should move a ticket to a new column after drag-and-drop", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const card = page.locator("[data-testid='card-T4']");
		const targetColumn = page.locator("[data-testid='column-in-review'] [role='listbox']");
		await expect(card).toBeVisible();
		await dragCardToColumn(page, card, targetColumn);
		await expect(page.locator("[data-testid='column-in-review'] [data-testid='card-T4']")).toBeVisible();
	});

	test("should persist status change after page reload", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const card = page.locator("[data-testid='card-T4']");
		const targetColumn = page.locator("[data-testid='column-in-review'] [role='listbox']");
		await dragCardToColumn(page, card, targetColumn);
		await expect(page.locator("[data-testid='column-in-review'] [data-testid='card-T4']")).toBeVisible();
		await page.reload();
		await expect(page.locator("[data-testid='column-in-review'] [data-testid='card-T4']")).toBeVisible();
	});

	test("should update column counts after drag-and-drop", async ({ page }) => {
		await page.goto("/");
		await page.waitForLoadState("networkidle");
		const readyColumn = page.locator("[data-testid='column-ready']");
		const inReviewColumn = page.locator("[data-testid='column-in-review']");
		await expect(readyColumn.locator("h2 + span")).toHaveText("2");
		await expect(inReviewColumn.locator("h2 + span")).toHaveText("1");
		const card = page.locator("[data-testid='card-T4']");
		const targetColumn = inReviewColumn.locator("[role='listbox']");
		await dragCardToColumn(page, card, targetColumn);
		await expect(readyColumn.locator("h2 + span")).toHaveText("1");
		await expect(inReviewColumn.locator("h2 + span")).toHaveText("2");
	});
});
