import type { PageServerLoad } from "./$types.js";
import { loadTickets, ticketsByStatus } from "$lib/tickets.js";
import { TICKETS_DIRECTORY } from "$lib/server/tickets-dir.js";

export const load: PageServerLoad = () => {
	const tickets = loadTickets(TICKETS_DIRECTORY);
	return { columns: ticketsByStatus(tickets) };
};
