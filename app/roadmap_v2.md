# Core Shell — Product Roadmap to v2.0

## What v2.0 means

v1.0 was the infrastructure layer proven solid: launcher, database, config, credentials/API, event bus, registry, router — built, tested, hardened in a dedicated optimization pass.

**v2.0 is the same milestone one layer up: the first generation of utility modules built, real-world validated (not just synthetic-tested), and given the same kind of optimization/hardening pass the shell received.** Scheduler, meal planner, the YouTube silo, and a real UI are bigger, still-being-designed systems that come after v2.0, not inside it.

## Phase 1 — Small, unblocked bites

These have no dependency on anything else in this roadmap and no open design questions left. Pure execution.

1. **BPM calculator** — pure arithmetic. Given a source tempo, checks the original, doubled, and halved values against a 120 BPM target and computes whichever requires the smallest percentage speed change. No audio analysis, no dependencies beyond what already exists.
2. **Standalone silence-trimmer** — caps any silence stretch longer than a threshold. Deliberately does **not** merge with the breath-remover: silence-trimming is pure amplitude analysis and needs no VAD, so keeping it separate keeps it genuinely lighter (no `onnxruntime`/model dependency for a module that doesn't need one). Shares one small "cap silence duration" utility function with the breath-remover rather than duplicating that logic. **Open decision:** exact threshold (1.5s vs. 2s) still needs a final answer, or should be a configurable parameter.
3. **Cleanup orchestrator** — a thin wrapper that calls the breath-remover and silence-trimmer in sequence, giving the "one button" feel without merging their internals.

## Phase 2 — Validation and a small new feature

4. **Breath-remover real-world validation** — not really "sequenced" against the rest; runs in parallel whenever real narration samples are available to test against. The mechanical pipeline is already rigorously verified (bit-for-bit matched against the reference VAD implementation, exact sample-level reassembly correctness); what's unverified is real-world detection accuracy on an actual voice, which can't be closed from spec work alone.
5. **Splitter Bot** — an app feature, not a live process-oversight mechanism (that question was explicitly considered and resolved: the splitting function is currently well-served by conversation itself, and formalizing it now would add overhead without a clear gain). As a feature, it maps directly onto the existing content-maturity taxonomy: takes a raw `thought`/`idea`-stage entry, breaks it into discrete tasks via an API call, flags which are mechanical vs. which have real open design questions, and logs the result as a `concept`-stage entry. Buildable on infrastructure that already exists (`api_client.call()`, the `entries` table, the taxonomy stages).

## Phase 3 — Shared infrastructure the big systems need

6. **Notification/delivery system ("Crier")** — genuinely new infrastructure category, not an extension of anything built so far. Both meal planner (Sunday menu notification → confirm → shopping list notification) and scheduler (reminders, escalating attention-getting for important items) need this. Building it once, as shared infrastructure, avoids duplicating it per-system. Delivery mechanism (push notification, email, something else) is an open design question for when this gets built.

## Phase 4 — Meal Planner

Promoted ahead of Scheduler in this roadmap specifically because it has significantly more design resolution already worked out.

**Inputs (mostly static config, same shape as everything else in this system):** family presence/quantity per week, dietary restrictions/tastes per person, preferred meals per person, general nutrition guidelines, practical considerations (availability, cooking method/duration).

**Meal-plan generation, decomposed into pieces of appropriate difficulty** (the "does this need a smarter/more expensive model" concern raised earlier is resolved by this decomposition — nearly all of it turns out to be Haiku-tier or fully deterministic):
1. Hard-constraint filtering (allergies, restrictions) — pure deterministic filtering against a stored recipe list.
2. Scoring/ranking (past star ratings, recency, preference match, fridge-inventory fit) — weighted arithmetic, a basic recommender-system formula, not model reasoning.
3. Day-by-day assignment (avoid repeating proteins, balance cook time across the week) — mostly deterministic; possibly a narrow model call for tie-breaking variety.
4. **New recipe sourcing, when stored recipes don't cover the week** — deliberately **not** LLM-generated from scratch (recipes are exactly the content type where precise generation is riskiest — wrong quantities have real physical consequences, unlike a wrong file-sort guess). Instead: search the web for real, reviewed recipes matching the dish and constraints (Claude API's `web_search` tool), evaluate candidates, extract the best match into a structured format. Most major recipe sites publish `schema.org` Recipe markup specifically for this kind of parsing, making extraction more reliable than scraping raw text.

**Inventory tracking:** no camera- or weight-based food sensing (flagged as a genuinely unsolved consumer-hardware problem, not a v2.0-appropriate bet). Instead: a UPC barcode scan on putting groceries away (solved, mature tech for item *identification*) paired with **inferred depletion** — since the system already knows which meals were confirmed as actually cooked, it can subtract those ingredients from tracked inventory automatically, without needing any consumption-sensing hardware at all. Ad-hoc snacking outside planned meals becomes accepted drift, reconciled periodically by hand, not a blocking problem.

**Feedback loop:** Saturday star-rating (0–5 per meal made that week) feeds back into the scoring step in (2) above.

**Depends on:** the shared notification system (Phase 3) for the Sunday-menu / shopping-list flow.

## Phase 5 — Scheduler

Comes after Meal Planner specifically because its design still has open questions the meal planner's doesn't.

**Core mechanism:** a tiered-priority arbitration system (Redlines → Needs → Desires → Opportunities, framed as Id/Ego/Superego). Underneath the framing, this is a fairly standard tiered-priority pattern — the build should focus on the tier structure and arbitration rules; the psyche naming is meaningful to you but not new mechanics to design around.

**Genuinely exciting architectural finding:** the "sorter module" (classify calendar events into R/N/D by tag, or by inference when untagged) is structurally almost identical to the file organizer already built — deterministic tag match first, fuzzy model classification as fallback, human review if still unclear. Same `rule → local_llm → api → human` ladder, applied to calendar events instead of files. Strong evidence the router architecture generalizes well beyond file handling.

**Also genuinely interesting:** the time-distributor (fitting a priority list into available calendar hours) is structurally the same *kind* of problem as the meal planner's day-by-day assignment step (Phase 4, item 3) — both are constrained-assignment/bin-packing: ranked items, capacity-limited slots, hard and soft constraints. If both get built, a shared "assign ranked items to constrained slots" utility is worth considering, though the concrete constraint types differ enough (scheduler has fixed-time obligations like an appointment; meal planning doesn't) that the shared piece would need to stay fairly generic.

**New infrastructure this needs, not required by anything built so far:**
- Google Calendar API access — an entirely new credential category (OAuth, token refresh), unlike the Anthropic-only credential system that exists today.
- The time-distributor algorithm itself — meaningfully more algorithmically complex than anything built to date.
- The Crier module (Phase 3) for delivery/reminders/escalation.

## Explicitly parked, not forgotten

- **YouTube pipeline as a silo** — bookmarked from the very first conversation, no build trigger yet.
- **Real UI** — batch runs and module management stay config/CLI-driven until the underlying pieces (through v2.0) are solid. Still just one status page in the whole app, deliberately.
- **Boss Bot** — reconsidered specifically once there's autonomous multi-step automation running with less direct oversight per step (plausible once Splitter Bot, Meal Planner, and Scheduler are all live and firing notifications somewhat independently) — not a numbered phase, a condition to watch for.
- **GitHub `main` branch / releases push** — happens at your own defined v2.0 completion trigger, per your existing `moddev`-branch workflow. Nothing about the branch needs attention before then.
