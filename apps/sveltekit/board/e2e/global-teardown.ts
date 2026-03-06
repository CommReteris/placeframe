import { removeFixtureDirectory } from "./fixtures.js";

export default function globalTeardown(): void {
	removeFixtureDirectory();
}
