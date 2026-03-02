---
id: T42
title: Add context pollution guidance to workon RED phase
status: ready
depends_on: []
---

# T42: Add context pollution guidance to workon RED phase

## Goal

Explicitly instruct Claude to focus on requirements, not anticipated implementation, when writing tests in the RED phase.

## Context

Research on AI+TDD shows that when the same LLM context writes both tests and implementation, it tends to write tests that validate anticipated code structure rather than requirements. The workon skill has a human review gate after RED (which helps), but doesn't explicitly tell Claude to avoid this failure mode.

## Key files

- `.claude/skills/workon/SKILL.md` — step 4, RED phase

## Approach

Add to the RED phase instructions: "Focus exclusively on the 'Done when' criteria and spec behaviors. Do not consider implementation approach — the tests should encode requirements, not predicted code structure."

## Done when

- RED phase instructions explicitly direct Claude to focus on requirements over implementation
