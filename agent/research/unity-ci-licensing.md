# Unity CI Licensing: Seat Limits and Concurrent Activations

Research conducted 2026-03-04. Context: T75 adds win64 builds to CI — need to understand why 5 parallel Linux builds work with a single personal license, and whether Windows builds will too.

## The question

Why does serial-based activation allow 5+ parallel CI builds when Unity docs say 2 seats max? Will it scale to Windows? What breaks if Unity tightens enforcement?

Constraints: single Unity Personal license (serial-based), GameCI Docker containers, GitHub Actions hosted runners.

## Why Linux parallel builds work

**GameCI hardcodes a fixed `machine-id` in all Linux Docker images.**

From [`game-ci/docker/base/Dockerfile`](https://github.com/game-ci/docker/blob/0be9208/base/Dockerfile):

```dockerfile
RUN echo "576562626572264761624c65526f7478" > /etc/machine-id \
    && mkdir -p /var/lib/dbus/ \
    && ln -sf /etc/machine-id /var/lib/dbus/machine-id
```

Unity's licensing server identifies machines by hardware fingerprint, which includes `/etc/machine-id` on Linux. Because all GameCI containers report the same ID, Unity sees 5 containers as **one machine**. Each activation reuses the same activation slot rather than consuming a new one.

Additionally, GitHub's hosted runners all emit the same `HardwareId` (confirmed in [GameCI activation docs](https://game.ci/docs/1/github/activation/)), reinforcing the single-machine illusion.

This is **intentional on GameCI's part**, not a bug or undocumented tolerance. Their [Docker images docs](https://game.ci/docs/docker/docker-images/) explicitly state seat consumption is "not an issue for free licenses."

### The two log messages

The logs show both `Successfully activated the entitlement license` and `Successfully activated ULF license`. This is expected: Unity 6 command-line activation with `-serial -username -password` triggers both the legacy serial (ULF) and modern Named User License (entitlement) simultaneously. Both bind to the same machine identity. [Unity support confirms this dual-activation behavior.](https://support.unity.com/hc/en-us/articles/39229898813844)

## Windows is fundamentally different

**GameCI Windows containers do NOT hardcode a machine-id.** From [GameCI Windows Docker docs](https://game.ci/docs/docker/windows-docker-images/):

> "The Ubuntu base images use a hardcoded machine id whereas the Windows machines do not."
> "License files for every run are identical apart from the last four symbols of the machine hash code."
> "In Windows, it's necessary to acquire a license every time and return it after a building process."

Each Windows container generates a **different** machine hash, so each one counts as a distinct machine from Unity's perspective.

### Impact on T75

Current state: 5 Linux containers sharing 1 activation slot. If we add 2 Windows containers (Outernet.Client win64 + MapRegistrationTool win64):

| Machine identity | Activation slots consumed |
|---|---|
| All Linux GameCI containers (shared machine-id) | 1 |
| Windows container #1 (unique machine hash) | 1 |
| Windows container #2 (unique machine hash) | 1 |
| Dev machine (if Unity is open locally) | 1 |
| **Total** | **3–4** |

Unity allows **2 activations per serial**. Two parallel Windows containers would exceed the limit.

### Possible workaround: native runner activation

If win64 builds activate on the bare `windows-latest` runner (not inside a Docker container), all GitHub-hosted Windows VMs may share the same `HardwareId` — similar to how Linux runners work. This would mean both Windows builds share 1 slot. But this is speculative and untested.

### Known Windows container issues

- **DNS resolution failures** reaching Unity's licensing server ([game-ci/unity-builder#669](https://github.com/game-ci/unity-builder/issues/669))
- **IPC/token caching failures** during Windows IL2CPP activation ([game-ci/unity-builder#569](https://github.com/game-ci/unity-builder/issues/569))

## Hard ceiling

There is no documented ceiling on the number of containers sharing the same machine-id. The limit is on **distinct machine identities**: 2 per serial. All Linux containers share 1 identity, so 50 Linux containers would still use 1 slot. The constraint is Windows (each container = a new identity).

## Blast radius if Unity tightens enforcement

### Terms of service

Unity's [Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software) state:
- "You may only use one instance at any given time per seat"
- Build Server licenses are "not available with Unity Personal"
- Circumventing "capacity limits, Authorized User or storage limits" is prohibited

The GameCI machine-id trick is technically a terms violation. However:

### Enforcement likelihood

| Scenario | Likelihood | Impact |
|---|---|---|
| Block the known GameCI machine-id | Low | Thousands of projects break; GameCI rotates the ID |
| Add concurrent-instance-per-machine-id detection | Low | Breaks parallel builds for everyone |
| Deprecate serial-based activation entirely | Medium-High | Already migrating to Named User Licensing |
| Require Build Server license for CI (enforced) | Low-Medium | Would break every small team's CI |

**Most likely risk**: Unity deprecates serial activation in favor of entitlement-only, and the new system uses stricter device tracking that doesn't rely on `/etc/machine-id`. GameCI's hardcoded ID trick would stop working. The GameCI community is large enough that this would generate early warning.

**Enforcement history**: Unity has revoked Personal licenses for revenue threshold violations ($200K), but no documented cases of CI seat-count enforcement. The GameCI approach has been the status quo for years with Unity's awareness.

## Options for T75

| Option | Parallel win64? | Cost | Risk |
|---|---|---|---|
| **Serialize Windows builds** — run win64 jobs sequentially, activate/return before next | No | $0, adds wall-clock time | Low — stays within 2-seat limit |
| **Native runner activation** — don't use Docker containers for Windows, install Unity directly on `windows-latest` | Maybe — depends on shared HardwareId | $0, different architecture | Medium — untested assumption |
| **Second Personal license** — separate Unity account for CI | Yes | $0/year | Low — doubles available slots |
| **Unity Pro + Build Server** | Yes, properly | $2,640/year | None — officially supported |
| **GameCI Windows with sequential gate** — parallel Linux, sequential Windows with license handoff | Partial | $0 | Low |

## Sources

- [GameCI base Dockerfile (hardcoded machine-id)](https://github.com/game-ci/docker/blob/0be9208/base/Dockerfile)
- [GameCI Docker images docs (seat consumption)](https://game.ci/docs/docker/docker-images/)
- [GameCI Windows Docker images docs](https://game.ci/docs/docker/windows-docker-images/)
- [GameCI activation docs (GitHub VM HardwareId)](https://game.ci/docs/1/github/activation/)
- [Unity support: maximum license activations](https://support.unity.com/hc/en-us/articles/360040693532)
- [Unity support: duplicate activations from CLI](https://support.unity.com/hc/en-us/articles/39229898813844)
- [Unity support: license active on two devices](https://support.unity.com/hc/en-us/articles/39943726903060)
- [Unity license compliance](https://unity.com/pages/license-compliance)
- [Unity Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software)
- [game-ci/unity-builder#669 (Windows DNS issues)](https://github.com/game-ci/unity-builder/issues/669)
- [game-ci/unity-builder#569 (Windows IPC failures)](https://github.com/game-ci/unity-builder/issues/569)
