---
id: T72
title: Long-running jobs in Claude Code agent sessions
status: design-needed
depends_on: []
---

# T72: Long-running jobs in Claude Code agent sessions

## Goal

Enable Claude Code to reliably run jobs that take longer than 10 minutes (e.g. native C++ builds with vcpkg) and receive completion notifications.

## Context

The Bash tool's `timeout` parameter has a maximum of 600,000ms (10 minutes). The `run_in_background` flag sends a completion notification, but it's unclear whether background tasks are also subject to this timeout. During T69, the Cesium native build (cmake + vcpkg, ~30-60 minutes) could not be run through normal Claude Code mechanisms:

- `run_in_background: true` with `timeout: 600000` — notified on early failures but untested for long-running success (the build never succeeded within a session)
- `nohup` — runs indefinitely but sends no notification; Claude only learns the result when the user asks

This affects any job that takes more than ~10 minutes: native builds, large Docker image builds, full test suites, etc.

## Open questions

1. Does `run_in_background: true` enforce the timeout, or does it run until the process exits? If it doesn't enforce, the problem is already solved — just use `run_in_background` and accept the notification whenever it arrives.
2. If it does enforce: should we build a wrapper (e.g. a script that writes a completion marker file) so Claude can poll on user request? Or is "run it in a separate terminal" the right answer for >10min jobs?
3. Should the COI environment provide `screen` or `tmux` for this use case?
