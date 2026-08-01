# Module Status

Honest state of everything built. Updated as things change — this is a
living doc, not a changelog. Purpose: make "is this still relevant/actually
helping" visible at a glance, instead of something that has to be noticed
and raised manually.

**Status key:**
- 🟢 **Deployed & confirmed useful** — running on your machine, actually saving you something
- 🟡 **Built & tested, not yet in daily use** — works, but you haven't run it for real yet
- 🟠 **Built, not yet real-world validated** — tested against synthetic data only; the real question (does it work on your actual material) is still open
- ⚪ **Not built** — discussed/designed only

---

## Core infrastructure

Zero standalone value on its own — only matters if something built on top of it helps you. All 🟢 in the sense of "working correctly," but graded here on whether it's *load-bearing* for something real yet.

| Piece | Status | Notes |
|---|---|---|
| Launcher, DB, config, credentials, events, registry, router | 🟢 | Load-bearing for the file organizer, which is in real use |

## Modules

| Module | Status | Notes |
|---|---|---|
| **File organizer** | 🟢 | Running, watching a real folder, sorting real files. The one clear win so far. |
| **Duplicate file detector** | 🟡 | Built, tested, non-destructive. Not yet run on a real folder. |
| **Breath/noise remover** | 🟠 | Mechanically proven (exact sample-level correctness, VAD verified against reference implementation). Real-voice accuracy is genuinely untested — this is the next BPM-shaped risk: possible it's oversolved, undersolved, or unnecessary once actually tried. |
| **Standalone silence-trimmer** | ⚪ | Designed, not built. Threshold (1.5s vs 2s) still undecided. |
| **BPM/tempo calculator + detector** | ❌ Cancelled | Built, then found unnecessary — a manual downbeat-marking technique in Ableton solves the actual problem more simply. Kept here as a record, not a warning against building things, but a reminder to sanity-check "is there already a simple manual fix" earlier next time. |

## Bigger systems — design only, nothing built

| System | Status | Notes |
|---|---|---|
| Splitter Bot | ⚪ | Good conceptual fit (maps onto existing taxonomy), unbuilt |
| Notification/Crier shared service | ⚪ | Identified as needed by 2+ future systems, unbuilt |
| Meal Planner | ⚪ | Most design-resolved of the "big" systems, unbuilt |
| Scheduler | ⚪ | Real open design questions remain, unbuilt |

## Explicitly parked

Real UI, YouTube pipeline silo, GitHub `main` branch push — all intentionally deferred to their own stated triggers, not stalled.
