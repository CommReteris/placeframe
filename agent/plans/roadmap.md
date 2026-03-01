# Placeframe Roadmap

Single entry point for all planned work. Each ticket is self-contained with enough context for a cold-start session. Detail plans are in separate files.

CI-related tickets (T1-T8) share background context in `ci-background.md`.

Use `/workon` to pick up and work on a ticket. Use `/workon T4` to start a specific one.
Use `/roadmap` to create, import, query, or reorganize tickets.

**Status definitions:**
- **Blocked** — cannot start; reason stated
- **Design needed** — open questions must be discussed with user before planning
- **Plan needed** — enter plan mode, write implementation plan, get user approval
- **Ready** — approved plan exists, start implementing
- **Done** — implemented and verified

---

## Tickets

### T1: Add linting, formatting, and typechecking to CI

- **Status:** Plan needed
- **Detail:** `t1-linting-ci.md`
- **Depends on:** Nothing.

---

### T2: Local registry mode for build.py

- **Status:** Plan needed
- **Detail:** `t2-local-registry.md`
- **Depends on:** Nothing.

---

### T3: Snapshot tests for build.py argument assembly

- **Status:** Plan needed
- **Detail:** `t3-snapshot-tests.md`
- **Depends on:** T2

---

### T4: Branch-based builds and .env.lock strategy

- **Status:** Ready
- **Detail:** `t4-branch-based-builds.md`
- **Depends on:** Nothing.

---

### T5: Integration tests for API service

- **Status:** Design needed
- **Detail:** `t5-api-tests.md`
- **Depends on:** Nothing.

---

### T6: Integration tests for reconstruction and localization pipelines

- **Status:** Design needed
- **Detail:** `t6-ml-pipeline-tests.md`
- **Depends on:** T5

---

### T7: Unity client builds with GameCI

- **Status:** Blocked
- **Detail:** `t7-unity-ci.md`
- **Depends on:** Nothing.

---

### T8: GitHub Actions vendor risk mitigation

- **Status:** Blocked
- **Detail:** `t8-vendor-risk.md`
- **Depends on:** Nothing.

---

### T9: Unity 2022.3 LTS compatibility

- **Status:** Ready
- **Detail:** `t9-unity-2022-lts.md`
- **Depends on:** Nothing.

---

### T10: ZED capture Docker images + Renovate

- **Status:** Ready
- **Detail:** `t10-zed-docker-images.md`
- **Depends on:** Nothing.

---

### T11: SVO video capture refactor

- **Status:** Ready
- **Detail:** `t11-svo-video.md`
- **Depends on:** T10

---

### T12: Zero-internet ZED deployment script

- **Status:** Ready
- **Detail:** `t12-zed-deploy-script.md`
- **Depends on:** T10

---

### T13: ZED hardware documentation

- **Status:** Ready
- **Detail:** `t13-zed-hardware-docs.md`
- **Depends on:** T12

---

### T14: Codebase sweep — harvest TODOs into tickets

- **Status:** Plan needed
- **Detail:** `t14-codebase-sweep.md`
- **Depends on:** Nothing.

---

### T15: Create /intake skill

- **Status:** Done
- **Detail:** `t15-intake-skill.md`
- **Depends on:** Nothing.

---

### T16: Kanban board web UI

- **Status:** Done
- **Detail:** `t16-kanban-board.md`
- **Depends on:** T17

---

### T17: /workon skill with TDD workflow and frontmatter system

- **Status:** Ready
- **Detail:** `t17-workon-tdd.md`
- **Depends on:** Nothing.

---
