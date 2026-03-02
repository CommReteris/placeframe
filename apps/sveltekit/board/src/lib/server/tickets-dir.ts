import path from "node:path";

export const TICKETS_DIRECTORY =
	process.env["BOARD_TICKETS_DIR"] ?? path.resolve(process.cwd(), "../../../agent/tickets");
