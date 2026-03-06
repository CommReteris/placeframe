import { defineConfig } from "@playwright/test";
import { FIXTURE_DIR } from "./e2e/fixtures.js";

export default defineConfig({
	testDir: "e2e",
	workers: 1,
	fullyParallel: false,
	forbidOnly: !!process.env["CI"],
	retries: process.env["CI"] ? 2 : 0,
	globalSetup: "e2e/global-setup.ts",
	globalTeardown: "e2e/global-teardown.ts",
	use: {
		baseURL: "http://localhost:5173",
		trace: "on-first-retry",
	},
	projects: [
		{
			name: "chromium",
			use: { browserName: "chromium" },
		},
	],
	webServer: {
		command: "pnpm dev",
		url: "http://localhost:5173",
		reuseExistingServer: !process.env["CI"],
		env: {
			BOARD_TICKETS_DIR: FIXTURE_DIR,
		},
	},
});
