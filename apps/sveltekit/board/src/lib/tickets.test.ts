import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import {
	type Ticket,
	type Status,
	STATUSES,
	STATUS_LABELS,
	parseFrontmatter,
	dumpFrontmatter,
	loadTickets,
	loadTicket,
	updateTicketStatus,
	ticketsByStatus,
} from "./tickets.js";

function makeFrontmatter(fields: {
	id?: string;
	title?: string;
	status?: string;
	depends_on?: string[];
}): string {
	const id = fields.id ?? "T1";
	const title = fields.title ?? "Test ticket";
	const status = fields.status ?? "ready";
	const depends = fields.depends_on ?? [];
	const depsStr =
		depends.length === 0
			? "[]"
			: `[${depends.map((d) => `${d}`).join(", ")}]`;
	return `---\nid: ${id}\ntitle: ${title}\nstatus: ${status}\ndepends_on: ${depsStr}\n---\n`;
}

function makeTicketFile(
	id: string,
	title: string,
	status: string,
	depends: string[] = [],
): string {
	return `${makeFrontmatter({ id, title, status, depends_on: depends })}
# ${id}: ${title}

## Goal

Test goal for ${id}.
`;
}

describe("STATUSES", () => {
	it("should contain all five lifecycle statuses in order", () => {
		expect(STATUSES).toEqual([
			"blocked",
			"design-needed",
			"plan-needed",
			"ready",
			"done",
		]);
	});
});

describe("STATUS_LABELS", () => {
	it("should map every status to a human-readable label", () => {
		expect(STATUS_LABELS["blocked"]).toBe("Blocked");
		expect(STATUS_LABELS["design-needed"]).toBe("Design needed");
		expect(STATUS_LABELS["plan-needed"]).toBe("Plan needed");
		expect(STATUS_LABELS["ready"]).toBe("Ready");
		expect(STATUS_LABELS["done"]).toBe("Done");
	});
});

describe("parseFrontmatter", () => {
	it("should parse valid YAML frontmatter and return metadata and body", () => {
		const text = `---\nid: T1\ntitle: Test\nstatus: ready\ndepends_on: []\n---\n# Body content`;
		const result = parseFrontmatter(text);
		expect(result.metadata["id"]).toBe("T1");
		expect(result.metadata["title"]).toBe("Test");
		expect(result.metadata["status"]).toBe("ready");
		expect(result.body).toBe("# Body content");
	});

	it("should return empty metadata when text has no frontmatter", () => {
		const text = "# Just a heading\n\nSome content.";
		const result = parseFrontmatter(text);
		expect(result.metadata).toEqual({});
		expect(result.body).toBe(text);
	});

	it("should handle depends_on with multiple entries", () => {
		const text = `---\nid: T5\ntitle: Dep test\nstatus: blocked\ndepends_on: [T1, T3]\n---\nBody`;
		const result = parseFrontmatter(text);
		expect(result.metadata["depends_on"]).toEqual(["T1", "T3"]);
	});

	it("should handle multiline body content", () => {
		const text = `---\nid: T1\ntitle: Test\nstatus: ready\ndepends_on: []\n---\nLine 1\nLine 2\nLine 3`;
		const result = parseFrontmatter(text);
		expect(result.body).toBe("Line 1\nLine 2\nLine 3");
	});
});

describe("dumpFrontmatter", () => {
	it("should produce valid frontmatter string from metadata and body", () => {
		const metadata = {
			id: "T1",
			title: "Test",
			status: "ready",
			depends_on: [] as string[],
		};
		const result = dumpFrontmatter(metadata, "# Body");
		expect(result).toContain("---\n");
		expect(result).toContain("id: T1");
		expect(result).toContain("# Body");
	});

	it("should roundtrip through parse and dump", () => {
		const original = `---\nid: T3\ntitle: Roundtrip\nstatus: plan-needed\ndepends_on: [T1, T2]\n---\n# Content`;
		const parsed = parseFrontmatter(original);
		const dumped = dumpFrontmatter(parsed.metadata, parsed.body);
		const reparsed = parseFrontmatter(dumped);
		expect(reparsed.metadata["id"]).toBe("T3");
		expect(reparsed.metadata["status"]).toBe("plan-needed");
		expect(reparsed.body).toBe("# Content");
	});
});

describe("loadTicket", () => {
	let tempDir: string;

	beforeEach(() => {
		tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "board-test-"));
	});

	afterEach(() => {
		fs.rmSync(tempDir, { recursive: true });
	});

	it("should load a ticket from a file path", () => {
		const filePath = path.join(tempDir, "t1-test.md");
		fs.writeFileSync(filePath, makeTicketFile("T1", "Test ticket", "ready"));

		const ticket = loadTicket(filePath);
		expect(ticket.id).toBe("T1");
		expect(ticket.title).toBe("Test ticket");
		expect(ticket.status).toBe("ready");
		expect(ticket.dependsOn).toEqual([]);
		expect(ticket.body).toContain("# T1: Test ticket");
		expect(ticket.filePath).toBe(filePath);
	});

	it("should parse depends_on into dependsOn array", () => {
		const filePath = path.join(tempDir, "t5-deps.md");
		fs.writeFileSync(
			filePath,
			makeTicketFile("T5", "Deps test", "blocked", ["T1", "T3"]),
		);

		const ticket = loadTicket(filePath);
		expect(ticket.dependsOn).toEqual(["T1", "T3"]);
	});
});

describe("loadTickets", () => {
	let tempDir: string;

	beforeEach(() => {
		tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "board-test-"));
	});

	afterEach(() => {
		fs.rmSync(tempDir, { recursive: true });
	});

	it("should load all ticket files from a directory sorted by number", () => {
		fs.writeFileSync(
			path.join(tempDir, "t2-second.md"),
			makeTicketFile("T2", "Second", "ready"),
		);
		fs.writeFileSync(
			path.join(tempDir, "t1-first.md"),
			makeTicketFile("T1", "First", "done"),
		);
		fs.writeFileSync(
			path.join(tempDir, "t10-tenth.md"),
			makeTicketFile("T10", "Tenth", "plan-needed"),
		);

		const tickets = loadTickets(tempDir);
		expect(tickets).toHaveLength(3);
		expect(tickets[0]?.id).toBe("T1");
		expect(tickets[1]?.id).toBe("T2");
		expect(tickets[2]?.id).toBe("T10");
	});

	it("should skip files without frontmatter", () => {
		fs.writeFileSync(
			path.join(tempDir, "t1-has-frontmatter.md"),
			makeTicketFile("T1", "Has frontmatter", "ready"),
		);
		fs.writeFileSync(
			path.join(tempDir, "t2-no-frontmatter.md"),
			"# Just a heading",
		);

		const tickets = loadTickets(tempDir);
		expect(tickets).toHaveLength(1);
		expect(tickets[0]?.id).toBe("T1");
	});

	it("should return empty array when directory has no ticket files", () => {
		const tickets = loadTickets(tempDir);
		expect(tickets).toEqual([]);
	});

	it("should ignore non-ticket files", () => {
		fs.writeFileSync(
			path.join(tempDir, "t1-ticket.md"),
			makeTicketFile("T1", "Ticket", "ready"),
		);
		fs.writeFileSync(
			path.join(tempDir, "roadmap.md"),
			"# Roadmap\nNot a ticket.",
		);
		fs.writeFileSync(
			path.join(tempDir, "ci-background.md"),
			"# CI Background",
		);

		const tickets = loadTickets(tempDir);
		expect(tickets).toHaveLength(1);
	});
});

describe("ticketsByStatus", () => {
	it("should group tickets by status with all columns present", () => {
		const tickets: Ticket[] = [
			{
				id: "T1",
				title: "One",
				status: "ready",
				dependsOn: [],
				body: "",
				filePath: "t1.md",
			},
			{
				id: "T2",
				title: "Two",
				status: "done",
				dependsOn: [],
				body: "",
				filePath: "t2.md",
			},
			{
				id: "T3",
				title: "Three",
				status: "ready",
				dependsOn: [],
				body: "",
				filePath: "t3.md",
			},
		];

		const grouped = ticketsByStatus(tickets);
		expect(grouped["blocked"]).toEqual([]);
		expect(grouped["design-needed"]).toEqual([]);
		expect(grouped["plan-needed"]).toEqual([]);
		expect(grouped["ready"]).toHaveLength(2);
		expect(grouped["done"]).toHaveLength(1);
	});

	it("should return empty arrays for all statuses when given empty list", () => {
		const grouped = ticketsByStatus([]);
		for (const status of STATUSES) {
			expect(grouped[status]).toEqual([]);
		}
	});
});

describe("updateTicketStatus", () => {
	let tempDir: string;

	beforeEach(() => {
		tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "board-test-"));
	});

	afterEach(() => {
		fs.rmSync(tempDir, { recursive: true });
	});

	it("should update the status in the ticket file", () => {
		const filePath = path.join(tempDir, "t1-test.md");
		fs.writeFileSync(filePath, makeTicketFile("T1", "Test", "ready"));

		updateTicketStatus("T1", "done", tempDir);

		const updated = loadTicket(filePath);
		expect(updated.status).toBe("done");
	});

	it("should preserve the body content after status update", () => {
		const filePath = path.join(tempDir, "t1-test.md");
		fs.writeFileSync(filePath, makeTicketFile("T1", "Test", "ready"));
		const originalBody = loadTicket(filePath).body;

		updateTicketStatus("T1", "done", tempDir);

		const updated = loadTicket(filePath);
		expect(updated.body).toBe(originalBody);
	});

	it("should throw when ticket id is not found", () => {
		fs.writeFileSync(
			path.join(tempDir, "t1-test.md"),
			makeTicketFile("T1", "Test", "ready"),
		);

		expect(() => updateTicketStatus("T99", "done", tempDir)).toThrow(
			"Ticket T99 not found",
		);
	});
});

describe("Status type", () => {
	it("should accept all valid status values", () => {
		const statuses: Status[] = [
			"blocked",
			"design-needed",
			"plan-needed",
			"ready",
			"done",
		];
		expect(statuses).toHaveLength(5);
	});
});
