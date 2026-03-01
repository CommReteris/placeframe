# Placeframe Roadmap

Single entry point for all planned work. Each ticket is self-contained with enough context for a cold-start session. Detail plans are in separate files.

CI-related tickets (T1-T8) share background context in `ci-background.md`.

Use `/ticket` to pick up and work on a ticket. Use `/ticket T4` to start a specific one.

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
- **Goal:** Run ruff, basedpyright, and deptry-check on every push and PR.
- **Depends on:** Nothing.

---

### T2: Local registry mode for build.py

- **Status:** Plan needed
- **Detail:** `t2-local-registry.md`
- **Goal:** `--registry` option for build.py to mirror CI caching behavior locally.
- **Depends on:** Nothing.

---

### T3: Snapshot tests for build.py argument assembly

- **Status:** Plan needed
- **Detail:** `t3-snapshot-tests.md`
- **Goal:** Test that build.py produces correct bake arguments without running builds.
- **Depends on:** T2 (code dependency — uses `--registry` paths).

---

### T4: Branch-based builds and .env.lock strategy

- **Status:** Ready
- **Detail:** `t4-branch-based-builds.md`
- **Goal:** Support multiple long-running branches where every tip commit has a correct `.env.lock`.
- **Depends on:** Nothing.

---

### T5: Integration tests for API service

- **Status:** Design needed
- **Detail:** `t5-api-tests.md`
- **Goal:** Automated tests for API endpoints against real database and storage backends.
- **Depends on:** Nothing.

---

### T6: Integration tests for reconstruction and localization pipelines

- **Status:** Design needed
- **Detail:** `t6-ml-pipeline-tests.md`
- **Goal:** End-to-end tests for the reconstruction and localization ML pipelines.
- **Depends on:** T5 (test patterns), GPU infrastructure (not a ticket).

---

### T7: Unity client builds with GameCI

- **Status:** Blocked: Unity client not ready
- **Detail:** `t7-unity-ci.md`
- **Goal:** Automated Unity builds in CI.
- **Depends on:** Nothing. T4 informs trigger strategy but doesn't block.

---

### T8: GitHub Actions vendor risk mitigation

- **Status:** Blocked: low priority, no urgency
- **Detail:** `t8-vendor-risk.md`
- **Goal:** Ensure CI logic is portable and not locked into GitHub Actions.
- **Depends on:** Nothing.

---

### T9: Unity 2022.3 LTS compatibility

- **Status:** Ready
- **Detail:** `t9-unity-2022-lts.md`
- **Goal:** Downgrade Unity packages and AndroidMobile from Unity 6 to 2022.3 LTS.
- **Depends on:** Nothing.

---

### T10: ZED capture Docker images + Renovate

- **Status:** Ready
- **Detail:** `t10-zed-docker-images.md`
- **Goal:** Dockerfile and bake targets for ZED capture, Renovate for auto-bumping base images.
- **Depends on:** Nothing.

---

### T11: SVO video capture refactor

- **Status:** Ready
- **Detail:** `t11-svo-video.md`
- **Goal:** Replace per-frame JPEG writes with SVO hardware-encoded video via NVENC.
- **Depends on:** T10 (Docker image needed for integration testing).

---

### T12: Zero-internet ZED deployment script

- **Status:** Ready
- **Detail:** `t12-zed-deploy-script.md`
- **Goal:** `uv run deploy-rig` to transfer Docker images to air-gapped ZED Box over USB.
- **Depends on:** T10 (Docker image needed for integration testing).

---

### T13: ZED hardware documentation

- **Status:** Ready
- **Detail:** `t13-zed-hardware-docs.md`
- **Goal:** Hardware BOM, cable connections, and one-command deployment in `zed/README.md`.
- **Depends on:** T12.

---

### T14: Codebase sweep — harvest TODOs into tickets

- **Status:** Plan needed
- **Detail:** `t14-codebase-sweep.md`
- **Goal:** One-time sweep to triage all TODO/FIXME/HACK comments and inline bug references into roadmap tickets. Enable Ruff `FIX002` to prevent bare TODOs going forward.
- **Depends on:** Nothing.

---

### T15: Create /intake skill

- **Status:** Done (superseded by T16)
- **Detail:** `t15-intake-skill.md`
- **Goal:** Reusable skill for importing work items from any external source (email, Linear, notes) into the roadmap.
- **Depends on:** Nothing.

---

### T16: Kanban board web UI

- **Status:** Ready
- **Detail:** `t16-kanban-board.md`
- **Goal:** SvelteKit kanban board at `apps/sveltekit/board/` for visual ticket management, plus `/roadmap` skill.
- **Depends on:** T17.

---

### T17: /workon skill with TDD workflow and frontmatter system

- **Status:** Ready
- **Detail:** `t17-workon-tdd.md`
- **Goal:** YAML frontmatter on all tickets, `/workon` skill with RED/GREEN/REFACTOR TDD phases, shared ticket-format and testing convention docs.
- **Depends on:** Nothing.
