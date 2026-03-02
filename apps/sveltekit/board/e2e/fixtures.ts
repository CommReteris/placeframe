import fs from "node:fs";
import path from "node:path";
import os from "node:os";

interface FixtureTicket {
	id: string;
	title: string;
	status: string;
	dependsOn?: string[];
	body: string;
}

const FIXTURE_TICKETS: FixtureTicket[] = [
	{
		id: "T1",
		title: "Blocked ticket",
		status: "blocked",
		dependsOn: ["T3"],
		body: "\n# T1: Blocked ticket\n\nThis ticket is blocked.\n",
	},
	{
		id: "T2",
		title: "Design needed ticket",
		status: "design-needed",
		body: "\n# T2: Design needed ticket\n\nNeeds design work.\n",
	},
	{
		id: "T3",
		title: "Plan needed ticket",
		status: "plan-needed",
		body: "\n# T3: Plan needed ticket\n\nNeeds a plan.\n",
	},
	{
		id: "T4",
		title: "Ready ticket alpha",
		status: "ready",
		body: "\n# T4: Ready ticket alpha\n\nReady to implement.\n\n## Details\n\n- Item one\n- Item two\n\n**Bold text** and *italic text* here.\n",
	},
	{
		id: "T5",
		title: "Ready ticket beta",
		status: "ready",
		body: "\n# T5: Ready ticket beta\n\nAlso ready.\n",
	},
	{
		id: "T6",
		title: "In review ticket",
		status: "in-review",
		body: "\n# T6: In review ticket\n\nAwaiting review.\n",
	},
];

function ticketToMarkdown(ticket: FixtureTicket): string {
	let frontmatter = `---\nid: ${ticket.id}\ntitle: ${ticket.title}\nstatus: ${ticket.status}\n`;
	if (ticket.dependsOn && ticket.dependsOn.length > 0) {
		frontmatter += `depends_on: [${ticket.dependsOn.join(", ")}]\n`;
	}
	frontmatter += "---";
	return frontmatter + ticket.body;
}

export const FIXTURE_DIR = path.join(os.tmpdir(), "board-e2e-fixtures");

export function writeFixtureTickets(): void {
	fs.mkdirSync(FIXTURE_DIR, { recursive: true });
	for (const ticket of FIXTURE_TICKETS) {
		const filename = `${ticket.id.toLowerCase()}-${ticket.title.toLowerCase().replaceAll(" ", "-")}.md`;
		fs.writeFileSync(path.join(FIXTURE_DIR, filename), ticketToMarkdown(ticket));
	}
}

export function removeFixtureDirectory(): void {
	if (fs.existsSync(FIXTURE_DIR)) {
		fs.rmSync(FIXTURE_DIR, { recursive: true });
	}
}

export { FIXTURE_TICKETS };
