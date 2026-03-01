import path from "node:path";
import { fileURLToPath } from "node:url";

const thisDir = path.dirname(fileURLToPath(import.meta.url));
export const PLANS_DIRECTORY = path.resolve(thisDir, "../../../../../agent/plans");
