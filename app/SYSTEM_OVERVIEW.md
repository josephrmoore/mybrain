# Core Shell — System Overview

What this system **is**, described plainly. Not a plan (see `roadmap_v2.md`
for how we get there) and not a status report (see `MODULE_STATUS.md` for
what's currently built vs. not). This doc should stay accurate to the
architecture regardless of how much of it exists yet.

## The shape of the system

```
Core Shell (the platform)
│
├─ Core services — shared infrastructure, usable by anything, owned by nothing
│   ├─ Database, Config, Credentials, Event Bus, Module Registry, Router
│   ├─ Comms — talks to you: notifications, calendar/time awareness, receiving input
│   └─ Local LLM wrapper / Claude API wrapper
│
└─ Silos — domain verticals, each a distinct area of your life
    ├─ File Lord — file organization & cleanup
    │   ├─ Brain: Project Collector
    │   ├─ Brain: Trashman
    │   └─ Brain: Content Detective
    ├─ Meal Planner (future)
    ├─ Scheduler (future)
    └─ YouTube Pipeline (bookmarked, not started)
```

Inside any Silo:

```
Brain      — coordinates a group of Partners + Controls toward one goal
  └─ Partner   — does the actual decision-making (calculation + logic)
        └─ Control  — pure calculation, no decisions, reused across Partners
```

## Definitions

| Term | Plain meaning | Example |
|---|---|---|
| **Silo** | Highest-level classification — a distinct area of your life the system handles. Silos don't share each other's data, only core services. | File Lord, Meal Planner |
| **Brain** | Within a Silo, a coordinating unit toward one goal. Doesn't do the work itself — groups the Partners/Controls that do. | Trashman (goal: free up disk space) |
| **Partner** | Does the actual decision-making — calculation *and* logic. | Duplicate Finder (decides which copy is the "keeper") |
| **Control** | Pure calculation, no decisions. Reusable across Partners. | "Get this file's creation date," "hash this file's contents" |
| **Core service** | Shared infrastructure any Silo/Brain/Partner can use, owned by no single domain. | Comms, the Claude API wrapper, the event bus |

## Two taxonomies fixed at the core (hardcoded, not config-editable)

Every Silo routes through these same two ladders — they're structural, not
per-domain choices:

1. **Content maturity:** `thought → idea → concept → project → product → record`
2. **Decision confidence:** `local (deterministic code) → local_llm → api → human`

Anything else — categories, extensions, thresholds, which files belong to
which Partner — is config, not architecture, and lives in `config.yaml`.

## Non-negotiable principles (apply everywhere, no exceptions per-Silo)

- **Nothing is ever hard-deleted.** Files move to review/trash folders; DB rows soft-delete.
- **Desktop-only, single machine, single user.** No sync, no auth, not designed around future multi-user needs.
- **API access is optional everywhere.** Every Partner must degrade gracefully with zero API key configured.

---

## Silo: File Lord

**Goal, in your own words:** spend as close to zero time as possible on
manual cleanup, keep files in an organized and intuitive state, and
maintain organized folders for existing creative projects.

| Brain | Goal | Runs against |
|---|---|---|
| **Project Collector** | Consolidate scattered project files (DaVinci, Ableton, FCPX, etc.) into one folder per project | Workspace + external archive drives |
| **Trashman** | Free up workspace space — duplicates, large files, stale files, temp files | Workspace drive only (archive drives are already organized, don't need sweeps) |
| **Content Detective** | Classify what a file actually *is* — your own creative work, purchased/existing media, or an important document | Workspace + external archive drives |

Full Brain → Partner → Control breakdown, current build status, and open
questions per Partner: see `file_lord_brain_partner_breakdown.md`.

---

## Core service: Comms

Not a Silo — it doesn't own domain content, it's infrastructure other
things call into, the same way the API wrapper or event bus are.

**What it does:** contacts you (notifications), reads calendar/time context,
and receives data back from you. Priority order for reaching you: iMessage,
then SMS, then email. System-to-you is the current priority; you-to-system
(sending data back in) comes after.

---

## Silos not yet started

- **Meal Planner** — design substantially resolved (see `roadmap_v2.md`), not built.
- **Scheduler** — real open design questions remain (tiered-priority arbitration, Calendar OAuth), not built.
- **YouTube Pipeline** — bookmarked from the first conversation, no build trigger yet.
