import { json, error } from "@sveltejs/kit";
import type { RequestHandler } from "./$types.js";
import { loadTickets, updateTicketStatus, STATUSES } from "$lib/tickets.js";
import { PLANS_DIRECTORY } from "$lib/server/plans-dir.js";

export const PATCH: RequestHandler = async ({ params, request }) => {
	const body = (await request.json()) as Record<string, unknown>;
	const newStatus = body["status"];

	if (
		typeof newStatus !== "string" ||
		!STATUSES.includes(newStatus as (typeof STATUSES)[number])
	) {
		error(400, `Invalid status. Must be one of: ${STATUSES.join(", ")}`);
	}

	try {
		updateTicketStatus(params.id, newStatus, PLANS_DIRECTORY);
	} catch (e) {
		if (e instanceof Error && e.message.includes("not found")) {
			error(404, e.message);
		}
		throw e;
	}

	const tickets = loadTickets(PLANS_DIRECTORY);
	const updated = tickets.find((t) => t.id === params.id);
	return json(updated);
};
