from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PLANS_DIRECTORY = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "plans"

STATUSES = ["blocked", "design-needed", "plan-needed", "ready", "done"]

STATUS_LABELS = {
    "blocked": "Blocked",
    "design-needed": "Design needed",
    "plan-needed": "Plan needed",
    "ready": "Ready",
    "done": "Done",
}


@dataclass
class Ticket:
    id: str
    title: str
    status: str
    depends_on: list[str]
    body: str
    file_path: Path


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---\n", 4)
    header = text[4:end]
    body = text[end + 5 :]
    return yaml.safe_load(header), body


def dump_frontmatter(metadata: dict[str, Any], body: str) -> str:
    header = yaml.dump(metadata, default_flow_style=False, sort_keys=False).rstrip("\n")
    return f"---\n{header}\n---\n{body}"


def load_ticket(path: Path) -> Ticket:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    return Ticket(
        id=metadata["id"],
        title=metadata["title"],
        status=metadata["status"],
        depends_on=metadata.get("depends_on", []),
        body=body,
        file_path=path,
    )


def load_tickets(directory: Path | None = None) -> list[Ticket]:
    directory = directory or PLANS_DIRECTORY
    tickets = []
    for path in sorted(directory.glob("t*.md"), key=_ticket_sort_key):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        tickets.append(load_ticket(path))
    return tickets


def _ticket_sort_key(path: Path) -> int:
    name = path.stem
    prefix = name.split("-")[0]
    return int(prefix[1:]) if prefix[1:].isdigit() else 0


def tickets_by_status(tickets: list[Ticket]) -> dict[str, list[Ticket]]:
    grouped: dict[str, list[Ticket]] = {status: [] for status in STATUSES}
    for ticket in tickets:
        grouped.setdefault(ticket.status, []).append(ticket)
    return grouped


def update_ticket_status(ticket_id: str, new_status: str, directory: Path | None = None) -> None:
    directory = directory or PLANS_DIRECTORY
    for path in directory.glob("t*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        metadata, body = parse_frontmatter(text)
        if metadata.get("id") == ticket_id:
            metadata["status"] = new_status
            path.write_text(dump_frontmatter(metadata, body), encoding="utf-8")
            return
    raise ValueError(f"Ticket {ticket_id} not found")


def generate_roadmap(tickets: list[Ticket], output_path: Path | None = None) -> str:
    output_path = output_path or (PLANS_DIRECTORY / "roadmap.md")
    lines = [
        "# Placeframe Roadmap",
        "",
        "Single entry point for all planned work. Each ticket is self-contained with enough context "
        "for a cold-start session. Detail plans are in separate files.",
        "",
        "CI-related tickets (T1-T8) share background context in `ci-background.md`.",
        "",
        "Use `/workon` to pick up and work on a ticket. Use `/workon T4` to start a specific one.",
        "Use `/roadmap` to create, import, query, or reorganize tickets.",
        "",
        "**Status definitions:**",
        "- **Blocked** — cannot start; reason stated",
        "- **Design needed** — open questions must be discussed with user before planning",
        "- **Plan needed** — enter plan mode, write implementation plan, get user approval",
        "- **Ready** — approved plan exists, start implementing",
        "- **Done** — implemented and verified",
        "",
        "---",
        "",
        "## Tickets",
    ]

    for ticket in tickets:
        lines.append("")
        lines.append(f"### {ticket.id}: {ticket.title}")
        lines.append("")
        lines.append(f"- **Status:** {STATUS_LABELS.get(ticket.status, ticket.status)}")
        lines.append(f"- **Detail:** `{ticket.file_path.name}`")
        if ticket.depends_on:
            lines.append(f"- **Depends on:** {', '.join(ticket.depends_on)}")
        else:
            lines.append("- **Depends on:** Nothing.")
        lines.append("")
        lines.append("---")

    text = "\n".join(lines) + "\n"
    output_path.write_text(text, encoding="utf-8")
    return text
