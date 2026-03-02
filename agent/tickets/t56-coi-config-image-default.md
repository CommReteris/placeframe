---
id: T56
title: "Upstream: open issue for COI config.toml defaults.image not being applied"
status: plan-needed
depends_on: []
---

# T56: Upstream: open issue for COI config.toml defaults.image not being applied

## Goal

Open an issue against [mensfeld/code-on-incus](https://github.com/mensfeld/code-on-incus) reporting that `[defaults] image = "..."` in `~/.config/coi/config.toml` is parsed but never wired up to the `--image` flag.

## Context

COI's `root.go` `PersistentPreRunE` applies `cfg.Defaults.Persistent` when the `--persistent` flag isn't explicitly set, but has no equivalent logic for `cfg.Defaults.Image`. The `imageName` variable stays `""` and `session/setup.go` falls back to the hardcoded `CoiImage = "coi"`.

Our `write_coi_config()` in `setup_agent_sandbox.py` writes `image = "coi-placeframe"` to the config, but it has no effect. We work around this in `agent_shell.py` by passing `--image coi-placeframe` explicitly.

## Key files

- `scripts/src/scripts/agent_shell.py` — `--image` workaround and comment to update
- `scripts/src/scripts/setup_agent_sandbox.py` — `write_coi_config()` writes the config that doesn't work

## Done when

- [ ] Upstream issue filed on mensfeld/code-on-incus
- [ ] Upstream issue URL linked back into `agent_shell.py` comment and this ticket
- [ ] Once upstream ships a fix, remove the `--image` workaround from `agent_shell.py`
