# Ticket Audit

Audit of all open tickets (not `done` or `in-review`) against the sizing guidelines in `.claude/skills/shared/ticket-format.md`.

Evaluated against: reviewability (~400 lines, ~60 min review), atomicity (one-sentence test, coupling test), recoverability (single session), context capacity (key files fit in working memory). Also checked for staleness and structural issues.

---

## Superseded / stale

| Ticket | Status | Issue | Recommendation |
|---|---|---|---|
| **T32** | ready | "Note shared ticket numbering convention in backfill-spec" — adding one line to a skill. No design decisions, no review value. | Too small for a ticket. Merge into T30/T31 or just do it directly. |

---

## Sizing issues

### Too big

| Ticket | Status | Issue | Recommendation |
|---|---|---|---|
| **T21** | design-needed | "Backfill specifications for all subsystems" — scope is unbounded. The ticket itself acknowledges "will likely be split into per-subsystem tickets." Fails reviewability (output is many SPEC.md files), recoverability (can't complete in one session), and atomicity (many unrelated subsystems). | Split during design phase into per-subsystem tickets. Keep T21 as a tracking/parent ticket or close it once children are created. |

### Too small (candidates for merge)

| Ticket | Status | Issue | Recommendation |
|---|---|---|---|
| **T30** | ready | "Add conflict resolution guidance to backfill-spec" — adds one paragraph to step 1. Small but involves a design decision (how to resolve conflicts). | Merge T30 + T31 into one ticket: "Improve backfill-spec edge case handling." Both modify the same skill, both are ready, and together they pass the atomicity test. |
| **T31** | ready | "Handle existing partial SPEC.md in backfill-spec" — adds a precondition check. Small but involves a design decision. | Merge with T30 (see above). |
| **T32** | ready | "Note shared ticket numbering convention" — one line addition. No design decision. | Too small. Do it as a drive-by when fixing T30/T31, or just do it now without a ticket. |

---

## Blocked tickets — staleness check

| Ticket | Status | Blocked on | Still valid? |
|---|---|---|---|
| **T6** | blocked | T5 (integration tests for API) | Valid. T5 is design-needed, T6 can't start without it. |
| **T7** | blocked | GameCI framework availability | Valid. External dependency, nothing changed. |
| **T27** | blocked | Upstream bug #26251 (disable-model-invocation) | Valid. Still blocked on upstream. Four skills identified for the flag (tidy-commits, allow-tool, debrief, backfill-spec). |
| **T29** | blocked | Upstream bug #18837 (allowed-tools enforcement) | Valid. Still blocked on upstream. |
| **T33** | blocked | Upstream context:fork bugs (#17283, #18394, #19751) | Valid. Still blocked on upstream. |
| **T52** | blocked | Claude Code plan mode UX | Valid. Still blocked on upstream. |
| **T57** | blocked | Upstream COI build script embedding | Valid. Still blocked on upstream. |

---

## Well-sized tickets (no issues)

These tickets pass all four sizing constraints and have proper structure:

**design-needed:**
- **T5**: Integration tests for API service — well-scoped to one service, design discussion will determine exact test count
- **T8**: GitHub Actions vendor risk mitigation — design-needed is correct, needs scoping discussion
- **T22**: Board live refresh — one feature, one subsystem
- **T23**: Board search filtering — extends one existing feature
- **T24**: Persist drawer width — small but has design decisions (persistence key, defaults, resize behavior)
- **T25**: Configure tickets directory — one env variable, one subsystem
- **T38**: Referential integrity for references — well-scoped, design-needed is correct

**plan-needed:**
- **T1**: Linting/formatting in CI — one coherent CI pipeline addition
- **T2**: Local registry mode for build.py — one feature to one script
- **T3**: Snapshot tests for build.py — one test suite for one script (depends on T2)
- **T14**: Codebase sweep for TODOs — one-time operation, output is tickets (depends on T21)
- **T56**: Upstream COI config issue — well-scoped, one upstream issue to file

**ready:**
- **T4**: Branch-based builds — one coherent CI strategy
- **T9**: Unity 2022.3 LTS compatibility — one coherent downgrade operation
- **T10**: ZED capture Docker images — one set of related Docker configs
- **T11**: SVO video capture refactor — one feature replacement (depends on T10)
- **T12**: Zero-internet ZED deployment — one script (depends on T10)
- **T13**: ZED hardware documentation — one doc rewrite (depends on T12)

---

## Summary of recommended actions

1. **Mark T27 as done** — work was completed in the skill audit
2. **Merge T30 + T31** into one ticket, absorb T32 as a drive-by line
3. **Keep T21 as-is** — it already acknowledges it will be split during design. The sizing issue is known and deferred to the design phase.
4. All other open tickets pass the sizing guidelines
