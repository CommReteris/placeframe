---
name: research
description: Open-ended brainstorming interview followed by web/codebase research, producing a report in agent/research/.
argument-hint: "[topic]"
---

Conduct a research session on a topic. The process is: understand the question deeply through conversation with the user, then go search, then write a report.

Takes an optional topic as argument: `/research spatial anchor formats`. If no argument is given, ask the user what they want to research.

## Step 1: Frame the question

Start with the topic and have a short open-ended conversation to understand what the user actually needs to know. The goal is to leave this step with a sharp research question (or small set of questions) and clear criteria for what a useful answer looks like.

Ask questions like:
- What's the context? Why does this matter right now?
- What do you already know or suspect?
- What would a useful answer look like — a comparison table, a recommendation, a list of options, a deep dive on one thing?
- Are there constraints that narrow the search? (e.g., FOSS only, must work with Python, must self-host)
- What's out of scope? What should I *not* spend time on?

This is a conversation, not a checklist. Follow the thread where it goes. Some topics need 2 exchanges, some need 10. Let the user's energy guide the depth — if they're giving long answers full of context, keep asking. If they give short answers, they've said what they need to say.

**Do not start searching until the user confirms the research question is well-framed.** Summarize the question and scope back to them and get a "yes, go" before moving on.

## Step 2: Search

Now go find things. Use a mix of:
- **Web search** for external tools, libraries, prior art, community patterns, comparisons
- **Codebase exploration** for understanding current state, existing conventions, integration points
- **Web fetch** to read specific pages, docs, or READMEs in depth

Search broadly first, then drill into the most promising leads. Follow references — if a blog post mentions a tool, go read the tool's README. If a GitHub repo looks relevant, check its license, governance, last commit date, and star count.

Keep notes internally as you go. Don't narrate the search to the user — just do it. If you hit a dead end or a surprising finding that changes the direction, mention it briefly, but the user doesn't need a play-by-play.

**Search until you have enough to write a useful report.** For a narrow question this might be 5 minutes of searching. For a broad survey it might be much longer. The bar is: would the user learn something non-obvious from the report that they couldn't get from a single Google search?

## Step 3: Write the report

Write the report to `agent/research/{slug}.md`. The slug should be descriptive kebab-case (e.g., `spatial-anchor-formats.md`, `svelte-testing-libraries.md`).

**Report format** (adapt to fit the topic — these are common sections, not a rigid template):

```markdown
# {Title}

Research conducted {date}. Context: {one-line context from Step 1}.

## The question

{Sharp research question from Step 1, plus any constraints/scope.}

## {Findings — structure varies by topic}

{For a tool comparison: sections per tool/approach with assessment.}
{For a deep dive: narrative sections building understanding.}
{For a survey: grouped findings with cross-cutting analysis.}

## {Assessment / Recommendation / Conclusion}

{What does this mean for the project? What's the recommendation?}

## Sources

{List of URLs consulted, with brief descriptions.}
```

Guidelines:
- Write for a reader who wasn't in the brainstorming session. The report should stand alone.
- Include concrete details — version numbers, license types, last commit dates, governance models. Vague impressions are not useful.
- When comparing options, use tables for at-a-glance comparison alongside prose for nuance.
- State what doesn't fit and why, not just what does. Ruling things out is valuable.
- If the FOSS-only constraint from CLAUDE.md applies, evaluate governance and funding model for every tool considered.

After writing, offer to `/commit`.

## Step 4: Debrief

After the report is written, briefly tell the user what you found most interesting or surprising. If the research surfaced actionable next steps (a tool to try, a convention to adopt, a ticket to create), mention them. Keep it to 2-3 sentences — the report has the details.
