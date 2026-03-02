import { writeFixtureTickets } from "./fixtures.js";

export default function globalSetup(): void {
	writeFixtureTickets();
}
