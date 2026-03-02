import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";

export const STATUSES = [
	"blocked",
	"design-needed",
	"plan-needed",
	"ready",
	"done",
] as const;

export type Status = (typeof STATUSES)[number];

export const STATUS_LABELS: Record<Status, string> = {
	blocked: "Blocked",
	"design-needed": "Design needed",
	"plan-needed": "Plan needed",
	ready: "Ready",
	done: "Done",
};

export interface Ticket {
	id: string;
	title: string;
	status: Status;
	dependsOn: string[];
	body: string;
	filePath: string;
}

export function parseFrontmatter(text: string): {
	metadata: Record<string, unknown>;
	body: string;
} {
	if (!text.startsWith("---\n")) {
		return { metadata: {}, body: text };
	}
	const endIndex = text.indexOf("\n---\n", 4);
	if (endIndex === -1) {
		return { metadata: {}, body: text };
	}
	const header = text.slice(4, endIndex);
	const body = text.slice(endIndex + 5);
	return { metadata: YAML.parse(header) as Record<string, unknown>, body };
}

export function dumpFrontmatter(
	metadata: Record<string, unknown>,
	body: string,
): string {
	const header = YAML.stringify(metadata).trimEnd();
	return `---\n${header}\n---\n${body}`;
}

export function loadTicket(filePath: string): Ticket {
	const text = fs.readFileSync(filePath, "utf-8");
	const { metadata, body } = parseFrontmatter(text);
	const dependsOn = metadata["depends_on"];
	return {
		id: metadata["id"] as string,
		title: metadata["title"] as string,
		status: metadata["status"] as Status,
		dependsOn: Array.isArray(dependsOn) ? (dependsOn as string[]) : [],
		body,
		filePath,
	};
}

function ticketSortKey(filePath: string): number {
	const name = path.basename(filePath, ".md");
	const prefix = name.split("-")[0] ?? "";
	const numeric = prefix.slice(1);
	return /^\d+$/.test(numeric) ? parseInt(numeric, 10) : 0;
}

function findTicketFiles(directory: string): string[] {
	if (!fs.existsSync(directory)) {
		return [];
	}
	const results: string[] = [];
	for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
		if (entry.isDirectory()) {
			results.push(...findTicketFiles(path.join(directory, entry.name)));
		} else if (/^t\d+.*\.md$/.test(entry.name)) {
			results.push(path.join(directory, entry.name));
		}
	}
	return results;
}

export function loadTickets(directory: string): Ticket[] {
	const files = findTicketFiles(directory).sort(
		(a: string, b: string) => ticketSortKey(a) - ticketSortKey(b),
	);

	const tickets: Ticket[] = [];
	for (const filePath of files) {
		const text = fs.readFileSync(filePath, "utf-8");
		if (!text.startsWith("---\n")) {
			continue;
		}
		tickets.push(loadTicket(filePath));
	}
	return tickets;
}

export function ticketsByStatus(
	tickets: Ticket[],
): Record<Status, Ticket[]> {
	const grouped: Record<Status, Ticket[]> = {
		blocked: [],
		"design-needed": [],
		"plan-needed": [],
		ready: [],
		done: [],
	};
	for (const ticket of tickets) {
		const bucket = grouped[ticket.status];
		if (bucket) {
			bucket.push(ticket);
		}
	}
	return grouped;
}

export function updateTicketStatus(
	ticketId: string,
	newStatus: Status | string,
	directory: string,
): void {
	for (const filePath of findTicketFiles(directory)) {
		const text = fs.readFileSync(filePath, "utf-8");
		if (!text.startsWith("---\n")) {
			continue;
		}
		const { metadata, body } = parseFrontmatter(text);
		if (metadata["id"] === ticketId) {
			metadata["status"] = newStatus;
			fs.writeFileSync(filePath, dumpFrontmatter(metadata, body), "utf-8");
			return;
		}
	}
	throw new Error(`Ticket ${ticketId} not found`);
}
