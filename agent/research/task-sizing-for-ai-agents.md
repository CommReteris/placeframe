# Task/Ticket Sizing for AI Coding Agents

Research conducted 2026-03-02. Context: designing ticket sizing heuristics for the Placeframe roadmap, where the "developer" is an AI agent working in sessions with finite context.

## The question

What constraints determine the right size for a ticket when an AI agent implements it? Traditional sizing (story points, sprint fitting) doesn't apply. What does?

## Findings

### Four constraints on ticket size

Ordered by durability — the first two are permanent, the last two relax as tooling improves.

**1. Reviewability (human cognitive limit).** The output must be reviewable in one focused pass. The SmartBear/Cisco study (2,500 reviews, 3.2M lines) found defect detection drops sharply past ~400 lines at a pace of 300-400 lines/hour. Graphite's analysis (1.5M PRs) confirms: PRs with 200-400 lines have 40% fewer defects, small PRs get approved 3x faster. Ideal review session: under 60 minutes.

**2. Atomicity (logical coherence).** An atomic change "does one and only one thing" — describable in one sentence, revertable as a unit. The stacked diffs approach (Google, Meta) decomposes features into dependent chains of small changes. Key test: "Can I describe this diff in one sentence?" The coupling test disambiguates borderline cases: if the sentence has "and," would either half ship independently? If yes, split. If no, keep.

**3. Recoverability (session failure cost).** Cross-session state loss is fundamental for AI agents. Each new session starts fresh. Error isolation requires task isolation — a failed session loses at most one ticket's worth of work. Anthropic's guidance: if you've corrected Claude more than twice on the same issue, start a fresh session.

**4. Context capacity (agent working memory).** Performance degrades before the window fills (Chroma/Hong et al., 2025). METR's HCAST benchmark: agents succeed 70-80% on tasks humans complete in under 1 hour, dropping below 20% for 4+ hour tasks. SWE-Bench Pro confirms: on tasks averaging 107 lines across 4 files, even the best agents achieve only 15-23%. Anthropic's recommendation: scope work to one session.

### Decomposition heuristics

**Continue.dev's three-tier taxonomy** (most practical framework found):
- **Type 1 (Narrow)**: Feature flags, unit tests, boilerplate. One right answer, minimal context. Ideal agent tickets.
- **Type 2 (Context-dependent)**: Debugging, refactoring, optimization. Require right context but well-scoped.
- **Type 3 (Open-ended)**: "Build auth," "add photo upload." Must be decomposed into Type 1/2 first.

**The SASE paper (arXiv 2509.06216)** identifies the fundamental tradeoff: fine-grained decomposition improves focus but increases orchestration overhead; coarse-grained reduces management but risks context overload. Recommends adaptive granularity with human judgment.

### What does NOT matter

- Story points, sprint velocity, calendar-time estimation — irrelevant for agent sessions.
- "Can one developer do this in a day?" — wrong question. Right question: "Can this complete in one session and be reviewed in one pass?"
- T-shirt sizing (S/M/L) — too coarse to be useful.

## Sources

- [HCAST: Human-Calibrated Autonomy Software Tasks (METR)](https://arxiv.org/html/2503.17354v1)
- [SWE-Bench Pro](https://arxiv.org/html/2509.16941v1)
- [SASE: Agentic Software Engineering](https://arxiv.org/html/2509.06216v2)
- [SmartBear/Cisco Code Review Case Study](https://static0.smartbear.co/support/media/resources/cc/book/code-review-cisco-case-study.pdf)
- [Continue.dev: Stop Asking AI to Build the Whole Feature](https://blog.continue.dev/task-decomposition/)
- [Graphite: Code Review Best Practices](https://graphite.com/blog/code-review-best-practices)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)
- [Factory.ai: The Context Window Problem](https://factory.ai/news/context-window-problem)
- [Zylos Research: Long-Running AI Agents](https://zylos.ai/research/2026-01-16-long-running-ai-agents)
