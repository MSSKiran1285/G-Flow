# SapModelTest Product Backlog

This is the living source of truth for scope and progress. Update statuses and check off
acceptance criteria as work lands — that's how "where are we against the plan" stays
answerable from `git log`/`git diff` on this file, not from memory.

**Status legend:** ✅ Done · 🟡 Partial / in progress · ⬜ Not started

## Epic summary

| # | Epic | Status | Phase |
|---|---|---|---|
| 1 | Agent & Contract Foundation | ✅ Done | 0 |
| 2 | Universal Component Coverage | 🟡 Partial | 0 → 3 |
| 3 | Screen Scanning & Repository | 🟡 Partial | 0 → 4 |
| 4 | Test Authoring & Data-Driven Execution | 🟡 Partial | 0 → 1 |
| 5 | Chained Business Processes (Buffers) | 🟡 Partial | **1 (in progress)** |
| 6 | Master Data Mining & Test Data Generation | 🟡 Partial | 0 → 5 |
| 7 | Reporting & CI Integration | ⬜ Not started | 2 |
| 8 | Self-Healing Locators | ⬜ Not started | 4 |
| 9 | Business Process Modeling & MBT Generation | ⬜ Not started | 5 |
| 10 | AI Services | ⬜ Not started | 6 |
| 11 | Web Front End | ⬜ Not started | 7 |

Phase numbers reference the [Implementation Plan](#implementation-plan) below.

---

## Epic 1 — Agent & Contract Foundation

**Goal:** A versioned, UI-technology-agnostic gRPC contract and a working C# agent that
can open a SAP GUI session and execute typed actions against it.

**Status: ✅ Done**

- **US-1.1** — As a maintainer, I need one proto contract covering session lifecycle,
  scanning, and replay, so both sides of the agent boundary are generated from a single
  source of truth.
  - [x] `proto/uiadapter.proto` defines `ScanScreen`, `ExecuteAction`, `ExecuteBatch`,
        `ResolveLocator`, `Subscribe`, `CaptureScreenshot`, session lifecycle RPCs
  - [x] Every request carries `contract_version`; sensitive fields carry `masked`
  - [x] Codegen wired for both C# (build-time via Grpc.Tools) and Python (`grpc_tools.protoc`)

- **US-1.2** — As the agent, I need to reach a running SAP GUI session via COM without
  a locally-buildable interop assembly (none available in this environment).
  - [x] `Com/ComHandle.cs` uses `Type.InvokeMember`, not `dynamic` (confirmed live: SAP's
        registered type library isn't loadable, which broke `dynamic`'s DLR binding)
  - [x] `Marshal.BindToMoniker("SAPGUI")` reaches the running scripting engine

- **US-1.3** — As a tester, I need the agent to enforce a production guardrail so it can
  never be accidentally pointed at a disallowed system.
  - [x] `SapGuiConnectionManager` rejects sessions whose system isn't on the configured
        allowlist (empty allowlist = unrestricted, documented as a dev-only default)

---

## Epic 2 — Universal Component Coverage

**Goal:** Every SAP GUI Scripting component family (spec §5) is scannable and
replayable through one uniform contract.

**Status: 🟡 Partial** — dynpro families done; ALV grid read-only; everything else
(GuiTableControl, ALV write ops, Tree, TextEdit, other shells) unimplemented.

- **US-2.1** — Dynpro families (text input, selection, action, structure, window,
  statusbar) are fully scannable and replayable.
  - [x] `TextInputHandler`, `SelectionHandler`, `ActionHandler`, `StructureHandler`,
        `WindowHandler`, `StatusbarHandler` implemented and unit-tested (fakes)
  - [x] `SET_FOCUS` op works generically across every family (needed for F4 value help)
  - [x] Confirmed live: `SET`, `SEND_VKEY`, `PRESS`, `STATUSBAR_READ` all correct

- **US-2.2** — ALV grids (`GuiShell/GridView`) can be scanned for row/column metadata
  and read cell-by-cell — this is what table-browser mining (SE16N, VA05, ME2M) needs.
  - [x] `AlvGridHandler.EnrichSnapshot` populates `RowCount`/`VisibleRowCount`/`Columns`
  - [x] `GRID_GET_CELL` reads a specific (row, columnId) — confirmed live against
        SE16N/VBAK (500 rows, ~180 real columns, including custom Z-fields)
  - [ ] `GRID_SET_CELL`, row/column selection, toolbar/context-menu press — not built
  - [ ] Checkbox/button/link cell types — not built

- **US-2.3** — `GuiTableControl` (classic table control — VA01's item table, SE16N's
  field-selection table) is scanned with proper scroll math, not left `unmapped`.
  - [ ] Not started. **Known workaround in use today**: individual table-control cells
        are addressable as plain dynpro fields at a fixed `[col,row]` position (e.g. row
        0), which already works — but there's no generic row-count/scroll-position
        handling, so anything beyond the first visible row requires this epic.

- **US-2.4** — Trees, TextEdit, and other GuiShell subtypes (Calendar, Splitter,
  HTMLViewer, Office/Picture/Chart) are scanned and replayable per spec §5.
  - [ ] Not started.

---

## Epic 3 — Screen Scanning & Repository

**Goal:** A screen scanned once becomes a reusable, named `Module` with locator sets and
semantic names — the object-repository half of spec §3/§4.

**Status: 🟡 Partial** — persistence + basic scan works; no AI-enriched naming, no
review UI, no rescan/merge diffing.

- **US-3.1** — A live screen can be scanned and persisted as a `Module` with
  `ModuleAttribute`s, addressable later by semantic name.
  - [x] `smt scan-module` navigates, optionally pre-fills fields to reach a second
        screen, scans, and persists (`smt/repository/scanning.py`)
  - [x] Component ids are normalized to the short `wnd[0]/...` form before persisting
        (the full `/app/con[x]/ses[y]/...` scan output is tied to one session index —
        confirmed this breaks reuse, fixed)
  - [x] Confirmed live: `VA01_InitialScreen` (185 attrs), `VA01_ItemEntry` (561 attrs)

- **US-3.2** — Semantic names are derived automatically (from the SAP `Name` property),
  not just raw technical ids, so a TestCase author can read what a step actually does.
  - [x] `_semantic_name()` — collision-safe slug derivation
  - [ ] AI-enriched naming/descriptions/inferred domains (spec §4.2) — not started;
        current names are mechanical (e.g. `vbak_auart`), not "SalesDocumentType"

- **US-3.3** — A tester can review and approve a freshly-scanned Module before it's used
  in a TestCase (spec §4.2 "human approves before Ready").
  - [ ] Not started — no review workflow or UI; every scan is immediately usable

- **US-3.4** — Re-scanning a changed screen shows what changed and which TestCases are
  affected (spec §4.2 rescan/merge).
  - [ ] Not started — re-scanning today just overwrites the Module outright

---

## Epic 4 — Test Authoring & Data-Driven Execution

**Goal:** A functional tester can assemble a reusable TestCase from scanned Modules and
run it against a CSV of data rows.

**Status: 🟡 Partial** — CLI/YAML authoring + CSV-driven execution proven live; no UI,
no buffers/recovery, no reporting.

- **US-4.1** — A TestCase is authored as an ordered list of steps referencing Module
  attributes by semantic name, with per-step data bindings.
  - [x] `smt define-testcase` imports a YAML definition into the repository
        (`TestCase`/`TestStep`), re-import replaces the existing one by name
  - [x] Bindings: `literal:<value>` or `column:<TestSheet column>`
  - [x] A step can target a raw `component_id` directly (bypassing Module lookup) for
        elements that only exist conditionally, e.g. a completeness-check popup
  - [x] `optional: true` lets a step's missing component skip rather than fail the row

- **US-4.2** — A TestCase runs once per row of a CSV TestSheet, each row a fully
  independent session.
  - [x] `smt run-testcase` — proven live: two different real historical combinations
        each independently created and saved a distinct sales order (1976, 1977)
  - [x] Per-row pass/fail with the failing step index and the real SAP error message

- **US-4.3** — Test cases don't assume a starting screen — navigation is explicit.
  - [x] Documented + demonstrated: a TestCase must include its own `/n<tcode>` + Enter
        as ordinary steps (found live: a run failed until this was added)

- **US-4.4** — A tester can chain buffered values between steps within one TestCase
  (spec §6 `Buffer` ActionMode) — e.g. capture the created order number for use in a
  later step or a later TestCase.
  - [x] Done as part of Epic 5 — see US-5.1/US-5.2 for the actual capability and its
        live-testing status.

- **US-4.5** — Recovery scenarios (`on E-message → retry`, `on unexpected modal →
  screenshot + handler chain`, `on session loss → relogon + restart`) per spec §6.
  - [ ] Not started — a failed step today just fails the row.

---

## Epic 5 — Chained Business Processes (Buffers)

**Goal:** Prove the framework handles a real business *process*, not just one document
— the thing that actually differentiates this from a single-screen record/replay tool.

**Status: 🟡 Partial** — the engine capability is built and unit-tested; the live
VA01 → VL01N → VF01 chain is blocked on a real SAP master-data/customizing issue in this
sandbox, not a framework gap (see notes below each story).

- **US-5.1** — As a tester, I need a step's result (e.g. the created order number
  parsed from the statusbar) to be captured into a named buffer usable by later steps.
  - [x] `TestStep` gains `capture_buffer_key` / `capture_from` / `capture_pattern`;
        `smt/engine/executor.py` maintains a per-run buffer dict threaded through step execution
  - [x] Binding type `buffer:<name>` resolves from that dict, alongside `literal:`/`column:`
        (`smt/engine/message_patterns.py` supplies the regex extraction)
  - [x] Unit-tested: capture from `actual_value` and from a statusbar pattern; a mismatched
        pattern fails the row with a clear message instead of silently continuing

- **US-5.2** — As a tester, I need buffered values to survive across TestCases in a
  chain (VA01 → VL01N → VF01), not just within one.
  - [x] `run_chain()` + `smt run-chain` run several TestCases per data row sharing one
        buffer, stopping a row's chain at the first failing TestCase
  - [x] Unit-tested: a value captured by one TestCase is correctly bound by the next;
        a failure in the first TestCase stops the chain before the second ever opens a session
  - [ ] **Live 3-step proof blocked, not by the engine** — creating a *fresh* order that's
        immediately deliverable hit two real, since-fixed master-data quirks (a missing PO
        number, and plant `1000` being mislabeled "Std Plant US" but configured with
        country `GB`, which a material export/legal-control check rejects — switching to
        plant `1001`, genuinely US, fixed order creation: order 1978 saved cleanly on the
        first attempt). VL01N then hit a live "delivery split because of different shipping
        points" info-log for plant 1001 that never proceeds to an actual delivery — reading
        its long text needs `GRID_DOUBLE_CLICK_CELL`/row-select on ALV grids, which Epic 2
        hasn't built yet (M2 gap, tracked there). Stopped digging further rather than keep
        guessing this sandbox's shipping-point customizing blind.

- **US-5.3** — As a tester, I need the statusbar's message-pattern registry (spec §5)
  to auto-extract known document-number patterns, not require a hand-written regex per
  TestCase.
  - [x] Registry with `order_saved`, `delivery_saved`, `billing_saved` (`smt/engine/message_patterns.py`)
  - [x] `order_saved` confirmed live (orders 1976/1977/1978, all real "Standard Order N has
        been saved" statusbar text extracted correctly)
  - [ ] `delivery_saved` / `billing_saved` still `VERIFY-ON-TARGET` — no delivery has
        actually been created yet to confirm the real wording against (see US-5.2)

---

## Epic 6 — Master Data Mining & Test Data Generation

**Goal:** Test data comes from mining real, proven-valid combinations out of the SAP
system itself — not guesses, and not a separate manual extract.

**Status: 🟡 Partial** — two mining mechanisms proven live; not yet formalized into a
reusable "test data generation" service, no pairwise/boundary generation.

- **US-6.1** — Mine valid single-field domain values via F4 value help.
  - [x] `smt mine-o2c` / `smt mine-p2p` — order types, sales org/channel/division,
        vendors, all confirmed live
  - [x] Handles both single-popup and multi-step ("Restrict Value Range" search dialog)
        F4 flows
  - [x] Regression-tested: a banner row before the real header used to silently corrupt
        results (picked the wrong key column) — fixed with a shape-based heuristic

- **US-6.2** — Mine proven-valid *combinations* by reading real historical documents
  straight out of their tables, instead of guessing which independently-valid values
  actually go together.
  - [x] `smt read-table` (SE16N via the new ALV grid support) — confirmed live against
        VBAK/VBAP; this is what actually unblocked the order-1975/1976/1977 E2E proof
  - [x] Extended to LIKP/LIPS (deliveries) and T001W (plant master) while chasing the
        Epic 5 live chain — real historical delivery data (shipping point `0001`) and a
        real plant-master data quality issue (plant `1000` labeled "US", configured `GB`)
        both surfaced this way
  - [ ] VBRK/VBRP (invoices), EKKO/EKPO (purchase orders) — not yet exercised

- **US-6.3** — Pairwise/boundary/equivalence-class test data generation from a Module's
  attribute domains (spec §9).
  - [ ] Not started.

- **US-6.4** — P2P gets the same E2E proof O2C has (create + save a real PO).
  - [ ] Vendor mining done; purchasing org/group combinations not yet mined or proven —
        blocked on the same "read real historical EKKO/EKPO rows" approach as US-6.2

---

## Epic 7 — Reporting & CI Integration

**Goal:** Results are consumable by a human or a CI pipeline, not just CLI stdout.

**Status: ⬜ Not started**

- **US-7.1** — `smt run-testcase` can emit a JSON report (per-row status, message,
  timing) to a file, not just stdout.
- **US-7.2** — JUnit XML output so a CI pipeline can show pass/fail per row natively.
- **US-7.3** — An HTML report with a screenshot strip (spec §6) — needs `CaptureScreenshot`
  wired into the engine, which exists in the agent but isn't called by the executor yet.

---

## Epic 8 — Self-Healing Locators

**Goal:** A stale locator heals via semantic matching instead of failing the run (spec §7).

**Status: ⬜ Not started** — `ResolveLocator` is explicitly `Unimplemented` today (by
design, not oversight — flagged honestly rather than faked in M1).

- **US-8.1** — Exact-id and structural-pattern fallback strategies.
- **US-8.2** — Semantic-similarity fallback (embedding-based) against a delta scan.
- **US-8.3** — Healed steps report "passed (healed)" and open a reviewable proposal
  rather than silently patching the Module.

---

## Epic 9 — Business Process Modeling & MBT Generation

**Goal:** Generate TestCase skeletons from a modeled business-process graph, per spec §9.

**Status: ⬜ Not started.**

---

## Epic 10 — AI Services

**Goal:** NL test authoring, scan enrichment, failure triage, risk-based selection,
synthetic data generation (spec §8) — explicitly *outside* the deterministic execution
hot path.

**Status: ⬜ Not started.** No LLM provider has been chosen (deferred per earlier
conversation) — needs a decision before this epic can start.

---

## Epic 11 — Web Front End

**Goal:** A non-programmer tester can assemble and data-drive a test visually.

**Status: ⬜ Not started.** `core/api/` (FastAPI) and `core/ui/` (React) are still
empty placeholders. Explicitly deferred in favor of the CLI/config-driven path (Epics
3–5) per direct discussion — revisit once there's enough real usage to know what a UI
actually needs to support.

---

## Implementation Plan

Phases are sequenced by what each one unlocks for the next, not by the original spec's
M1–M7 numbering (which this backlog has partially reshuffled based on what turned out to
matter in practice — e.g. master-data mining came before self-healing because nothing
else works without real test data).

| Phase | Focus | Epics | Status |
|---|---|---|---|
| 0 | Foundation: contract, agent, dynpro+ALV-read coverage, repository/engine MVP, data mining | 1, 2 (partial), 3 (partial), 4 (partial), 6 (partial) | ✅ Done |
| **1** | **Chained business process**: buffers within and across TestCases, prove VA01→VL01N→VF01 end to end | 5 | 🟡 Engine done, live 3-step proof blocked on Epic 2 (ALV double-click/row-select) |
| 2 | Reporting: JSON/JUnit/HTML so results are usable outside a terminal | 7 | ⬜ |
| 3 | Full component coverage: GuiTableControl (real scroll math, not row-0-only), ALV write ops, Tree/TextEdit/other shells | 2 | ⬜ |
| 4 | Scanning maturity + self-healing: AI-enriched naming, review workflow, rescan/merge, locator healing | 3, 8 | ⬜ |
| 5 | MBT generation + generated test data: business-process modeling, pairwise/boundary generation, P2P E2E parity | 6, 9 | ⬜ |
| 6 | AI services: NL authoring, failure triage, risk-based selection (needs an LLM provider decision first) | 10 | ⬜ |
| 7 | Web front end | 11 | ⬜ |

**Phase 1 status:** the engine half is done — buffer capture, the message-pattern
registry, and `run_chain` cross-TestCase chaining are all built and unit-tested (27
passing tests). The live 3-step proof surfaced two real, now-fixed order-creation gaps
(missing PO number; plant `1000` mislabeled "US" but configured `GB`, which a material
export/legal-control check correctly rejected — plant `1001` fixed it, order 1978 saved
cleanly). It then hit a live VL01N "delivery split because of different shipping points"
info-log that never proceeds to an actual delivery; reading its long text needs
`GRID_DOUBLE_CLICK_CELL`/row-select on ALV grids, which Epic 2 doesn't have yet. Decision
point: either build that small ALV slice next (unblocks this directly) or accept the
engine-level proof as sufficient for now and revisit once Phase 3 (full component
coverage) lands anyway.
