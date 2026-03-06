---
id: T84
title: Design inlining audit policy and intentional-deviation tracking
status: design-needed
depends_on: []
---

# T84: Design inlining audit policy and intentional-deviation tracking

## Goal

Make the inlining/abstraction audit conventions produce the right outcome by default — aggressively inline, but don't nag about intentional structure — and define where intentional deviations are recorded so audits respect them.

## Context

The current audit conventions (#1 "inline aggressively" and #4 "no unnecessary abstractions") are marked as judgment calls. In practice, Claude is too conservative — defaulting to keeping single-use functions and variables rather than inlining them. The user wants a more aggressive default.

However, there are cases where single-use functions are the right organizational choice (e.g. `phase_clone`, `phase_codegen`, `phase_native_build` in the Cesium build script — each called once, but they ARE the structure of the file). The audit shouldn't flag these as violations when they were an intentional design choice.

## Open questions

- How to distinguish "justified single-use function" from "unnecessary abstraction" in audit guidance. Is there a heuristic beyond "the name clarifies something non-obvious"? (e.g. "the function represents a named phase/step in a pipeline" or "the function is >N lines and inlining would make the caller unreadable")
- Where to record intentional deviations so the audit step doesn't flag them. Options:
  - SPEC.md (per-directory or per-file) with a section listing accepted deviations
  - Inline comments (e.g. `# intentional: single-use function for pipeline structure`)
  - Nowhere — rely on Claude's judgment to recognize structural intent
- Should SPEC.md evolve toward a per-file concept (or at least per-directory with file-level notes)?
- Should the audit conventions stay "judgment" but with stronger default-to-inline language, or should they become "mechanical" with an explicit exceptions mechanism?
