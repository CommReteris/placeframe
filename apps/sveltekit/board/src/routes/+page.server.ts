import type { PageServerLoad } from "./$types.js";
import { loadTickets, ticketsByStatus } from "$lib/tickets.js";
import { PLANS_DIRECTORY } from "$lib/server/plans-dir.js";

export const load: PageServerLoad = () => {
	const tickets = loadTickets(PLANS_DIRECTORY);
	return { columns: ticketsByStatus(tickets) };
};
