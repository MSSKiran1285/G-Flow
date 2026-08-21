# BUILDER PROMPT: AI-First, Model-Based Test Automation Framework for SAP ECC (SAP GUI)
## Hybrid .NET/Python Architecture with Universal SAP GUI Component Coverage

> Copy everything below this line into your LLM / copilot code builder. It is written as a single, self-contained implementation brief. Feed it in full, then iterate milestone by milestone.

---

## 1. ROLE AND MISSION

You are a senior test-automation platform architect and full-stack engineer. Your mission is to design and implement **"SapModelTest" (working name)** — an AI-first, **model-based test automation (MBT) framework for SAP ECC accessed through SAP GUI for Windows**, conceptually similar to Tricentis Tosca, but built ground-up around LLMs and machine learning.

The framework must let functional SAP testers — not programmers — build, maintain, and execute robust regression suites for SAP ECC transactions (e.g., VA01, VA02, ME21N, ME22N, MIGO, MIRO, FB60, FB01, XD01, MM01, PA30, CJ20N) with:

1. **Separation of concerns (Tosca-style)**: technical UI details live in reusable **Modules**; business logic lives in **Test Cases** composed from modules; data lives in **Test Data Sheets / Test Case Design matrices**; execution lives in **Execution Lists**.
2. **Universal, lossless SAP GUI component coverage** — the framework's *primary differentiator and top requirement*. The screen scanner (object-repository builder) and the execution engine (replay) must both handle **every component type the SAP GUI Scripting API exposes** — classic dynpro controls *and* the full control-framework/GuiShell family (ALV grids, trees, toolbars, text editors, HTML viewers, calendars, splitters, tab strips, Office integration containers) — through one uniform component contract. If SAP GUI's own script recorder can touch it, this framework must scan it, model it, and replay against it. §5 defines the mandatory coverage matrix; treat it as an acceptance checklist.
3. **AI-first behavior at every layer**: NL-to-test authoring, intelligent scan enrichment, self-healing locators, risk-based test selection, synthetic test data generation, and LLM-assisted failure triage.
4. **Deterministic, auditable execution**: AI proposes; a deterministic engine executes and logs. No LLM call ever sits inside the hot execution path of a step unless the step explicitly opts into AI-assisted recovery.

Target environment: Windows, SAP GUI for Windows 7.70+ installed, SAP GUI Scripting enabled server-side (`sapgui/user_scripting = TRUE`) and client-side. Where you make a different justified technology choice than this brief, state the trade-off explicitly before coding.

---

## 2. ARCHITECTURE OVERVIEW: HYBRID .NET AGENT + PYTHON CORE

Implement as two cooperating processes with a versioned gRPC contract between them:

**(A) SapGuiAgent — C# / .NET 8 Windows service/console app.** Owns *all* COM interaction with SAP GUI Scripting via the early-bound interop assembly generated from `sapfewse.ocx` (SAPFEWSELib). Rationale: static typing over the full `GuiComponent` class hierarchy, compile-time safety, sane STA/COM apartment threading for parallel sessions, and single-binary deployment to Windows CI runners. The agent is deliberately thin and dumb: sessions, component tree serialization, typed component operations, events, screenshots. **No test logic, no AI, no persistence in the agent.**

**(B) Python 3.11+ Core.** Everything else: repository, scanner intelligence, modeling, execution engine, self-healing, AI services, data management, FastAPI backend, React UI, Typer CLI. Talks to the agent exclusively through the gRPC contract.

**(C) The gRPC contract (`uiadapter.proto`)** is the permanent abstraction boundary and must be UI-technology-agnostic in naming (this exact contract will later be implemented by a Playwright-based Fiori/UI5 agent). Core services:

```proto
service UiAgent {
  // Session lifecycle
  rpc ListConnections(Empty) returns (ConnectionList);
  rpc OpenSession(OpenSessionRequest) returns (SessionHandle);      // logon, multi-logon popup, language, client
  rpc CloseSession(SessionHandle) returns (Ack);
  rpc GetSessionInfo(SessionHandle) returns (SessionInfo);          // system, client, user, tcode, screen no, program

  // THE two capabilities everything hangs on:
  rpc ScanScreen(ScanRequest) returns (ScreenSnapshot);             // full/partial typed component tree — see §4
  rpc ExecuteAction(ActionRequest) returns (ActionResult);          // uniform typed replay op — see §5

  rpc ExecuteBatch(ActionBatch) returns (stream ActionResult);      // ordered steps, fail-fast or continue
  rpc ResolveLocator(LocatorRequest) returns (LocatorCandidates);   // scored candidates for self-healing
  rpc Subscribe(SessionHandle) returns (stream UiEvent);            // statusbar msgs, modal open/close, screen change, session loss
  rpc CaptureScreenshot(CaptureRequest) returns (ImageBlob);        // window / component-cropped
  rpc GetOkCodeHistory(SessionHandle) returns (OkCodeHistory);
}
```

Contract rules: protobuf messages are versioned (`contract_version` on every request); agent and core refuse to talk on mismatch; all component data crosses the wire as **typed protobuf messages, never opaque JSON strings**; sensitive values support a `masked` flag end-to-end. Provide a `FakeUiAgent` (Python, in-process) that replays recorded `ScreenSnapshot`/`ActionResult` fixtures so the entire core is testable without SAP or Windows.

Repo layout:

```
agent/                      # C# .NET 8 solution
  SapGuiAgent/
    Com/                    # interop wrappers, STA session threads
    Components/             # typed handlers per GuiComponent family (see §5)
    Scanning/               # tree walker, shell introspection, serializers
    Grpc/                   # service implementation
  SapGuiAgent.Tests/        # xUnit; COM mocked behind interfaces
core/                       # Python
  smt/
    adapter/                # gRPC client + FakeUiAgent + recorded fixtures
    repository/  scanner/  modeling/  engine/  healing/  ai/  data/
    api/  ui/  cli/  reporting/  prompts/
  tests/
proto/uiadapter.proto       # single source of truth, codegen for both sides
```

---

## 3. CORE DOMAIN CONCEPTS (Python core; implement as first-class entities)

Persisted via SQLAlchemy (SQLite MVP, PostgreSQL-ready, Alembic migrations), JSON export/import for Git-friendly diffing (one file per entity, deterministic key order), UUIDs, versions, audit fields.

| Entity | Purpose | Tosca analogue |
|---|---|---|
| `Module` | A scanned SAP screen/subscreen: technical metadata + `ModuleAttribute`s | Module (XScan) |
| `ModuleAttribute` | One control: component class, locator set, semantic name, label, domain, supported ActionModes | Module Attribute |
| `TestStep` | Module instance in a test case with per-attribute ActionMode + value/binding | TestStep |
| `TestCase` | Ordered TestSteps + preconditions + cleanup + expected results | TestCase |
| `TestCaseTemplate` + `TestSheet` | Template × N data rows → N instances | Test Case Design |
| `BusinessProcessModel` | Directed graph of screens/decisions; generates test cases via path coverage | (MBT differentiator) |
| `ExecutionList` | Ordered test instances + environment + schedule | Execution List |
| `ExecutionResult`/`StepResult` | Status, timings, screenshots, statusbar messages, buffers, healing events | Execution Results |
| `Buffer` | Runtime key-value store across steps/test cases | Buffer |
| `Requirement`/`RiskItem` | Risk weighting for test selection | Requirements & Risk |

---

## 4. ADVANCED SCREEN SCANNING (top-priority subsystem #1 — the object-repository builder)

The scanner must produce a **complete, typed, replayable model of any SAP GUI screen**, however complex. It runs in the agent (raw capture) + core (intelligence/enrichment).

### 4.1 Agent-side capture (`ScanScreen`)
- Recursive walk of the full component tree from any root (`wnd[0]`, a specific container, or all open windows including modals `wnd[1..n]`), emitting per component: scripting **Id**, **Type** and **TypeAsNumber**, **SubType** where applicable, Name, Text, Tooltip/DefaultTooltip, IconName, ScreenLeft/Top/Width/Height, Changeable, Modified, ContainerType flag, and every type-specific property listed in the §5 matrix.
- **GuiShell deep introspection** — non-negotiable. A `GuiShell` node must never be captured as an opaque leaf. Switch on `shell.SubType` and extract the full inner model: **GridView** (column ids, titles, tech names, order, RowCount/VisibleRowCount, CurrentCellRow/Column, selection mode, toolbar button ids+tooltips from `GetToolbarButtonId/…Tooltip`, cell types incl. checkbox/button/link cells); **Tree** (tree type — simple/list/column, column names, node keys+texts via `GetAllNodeKeys`/`GetNodeTextByKey`, hierarchy levels, item types, checkable/link items, context-menu availability); **Toolbar/TitleBar** (buttons, menus); **TextEdit** (full multiline text, line count); **HTMLViewer** (document title/URL; mark limited-scriptability honestly); **Calendar** (date range, selection interval); **Splitter/SplitterContainer** and **TabStripInShell** (recurse into panes/tabs); **Office/Picture/BarChart/ChartControl** (capture metadata, flag replay limitations). Unknown/rare subtypes are captured with raw property dumps and flagged `unmapped` — never silently dropped.
- **Table control completeness**: for `GuiTableControl`, capture column metadata (title, tech name from cell ids like `RV45A-MABNR`, fixed/scrollable), row count vs visible rows, and the **scrollbar model** (`VerticalScrollbar.Position/Maximum/PageSize`) so the core can compute absolute-row → visible-cell math. Optional exhaustive mode pages through scroll positions to capture all rows.
- **Tabstrip completeness**: enumerate all `GuiTab`s; optional deep-scan mode selects each tab in turn and scans its contents, restoring the original tab afterward. Same pattern for pressing "expand" style buttons the caller whitelists.
- **F4 metadata**: capture `IsHighlighted`, required-field indication, and whether a field offers value help; optionally open F4 (`Locking`-safe), scan the help modal, and close it — recording the value-help type.
- **Menu bar capture**: full `GuiMenubar` tree with paths (e.g., `System→Status`) so menus are modelable and replayable.
- Incremental scan: `ScanScreen(delta_since=snapshot_hash)` returns only changed subtrees (hash per subtree) — used by execution-time verification and drift detection to stay fast on 500+ control screens (target: full scan of such a screen < 2 s, delta scan < 200 ms).
- Every snapshot carries screen context: system/client, tcode, program, screen number, window title, window count/modal stack — this context is part of every attribute's fingerprint.

### 4.2 Core-side scanning intelligence
- `smt scan --tcode VA01 [--deep-tabs] [--record]`: drives to the transaction, requests snapshots, and emits draft `Module`s — one per logical screen/subscreen, with tables/grids/trees modeled as **structured attributes** (column-aware, row-addressable), not flattened cell lists.
- **Label resolution**: nearest-`GuiLabel` and left-label heuristics, tooltip fallback, DDIC-style tech-name parsing from ids (`VBAK-AUART` → table/field), tab-title + group-box context attached to each attribute.
- **AI enrichment pass** (LLM, never during execution): semantic names (`SalesDocumentType`), one-line descriptions, inferred domains (date, amount+currency, quantity+UoM, code-with-F4), suggested default ActionModes. Human approves in the UI before a module is "Ready".
- **Flow recorder**: record mode watches the user click through a transaction (agent streams `UiEvent`s + snapshots on each screen change), captures each distinct screen as a module draft and transitions as a draft `BusinessProcessModel`.
- **Rescan/merge**: three-way diff (old model / new scan / test usage) preserving semantic names, showing impacted test cases, per-attribute match scoring.
- Every `ModuleAttribute` stores a **locator set**, not one string: exact scripting Id, structural pattern (id with volatile indices parameterized), tech field name, label fingerprint, component type, tab/group context, relative position — the raw material for §7 self-healing.

## 5. UNIVERSAL COMPONENT COVERAGE MATRIX (top-priority subsystem #2 — execution replay)

Implement one typed handler per family in the agent, all conforming to a uniform interface: `Read`, `Set`, `Verify`, `Press/Select`, plus family-specific ops. `ExecuteAction` dispatches on component class. **This matrix is the acceptance checklist; every row needs handler + scan support + replay support + a recorded fixture test.**

| Family | Components | Mandatory replay operations |
|---|---|---|
| Text input | GuiTextField, GuiCTextField, GuiPasswordField | read/set text, caret position, verify, masked handling |
| Selection | GuiComboBox, GuiCheckBox, GuiRadioButton | select by key *and* by visible text; get state |
| Actions | GuiButton, GuiOkCodeField (`/n`,`/o` tcodes), GuiMenubar/GuiMenu (path-based select), GuiToolbar | press; send VKeys (Enter, F3, F8, Ctrl+S…); menu path invoke |
| Structure | GuiTabStrip/GuiTab, GuiSimpleContainer, GuiScrollContainer (scroll ops), GuiUserArea, GuiBox, GuiLabel (read/verify; label grids in list screens) | tab select; container-relative resolution |
| Windows | GuiMainWindow, GuiModalWindow, GuiFrameWindow | maximize/resize; modal detect + handle stack; close; title verify |
| Statusbar | GuiStatusbar | read type/text/MessageId/Number; double-click to open long text; **message-pattern registry** auto-extracts created doc numbers into buffers |
| Table control | GuiTableControl | absolute-row get/set with automatic scroll math; row select; column ops; ConfigureLayout; find-row-by-predicate across pages |
| ALV Grid | GuiShell/GridView | getCellValue/setCellValue by row + column-id; selectRow(s)/columns; currentCell; doubleClick cell; press toolbar/context-toolbar button; context menu select; checkbox/button/link cells; setFilter-equivalent via toolbar+modal choreography; scroll (firstVisibleRow); export-safe iteration of all rows |
| Trees | GuiShell/Tree (simple, list, column) | expand/collapse by key; select node/item; double-click; check checkbox items; click link items; context menu; column-tree cell read |
| Text | GuiShell/TextEdit | get/set full text; line ops; verify contains/regex |
| Other shells | Toolbar, HTMLViewer, Calendar (select date/interval), Splitter (sash position), TabStripInShell, Office/Picture/Chart | implement what the API allows; where scripting is limited, degrade explicitly: raise `UnsupportedOperation` with guidance + offer coordinate-click fallback flagged `fragile:true` in results |
| Legacy/batch | SendVKey on any window; OK-code navigation; SAP Easy Access favorites tree | full keyboard-path replay so *anything* reachable by keys is automatable |

Cross-cutting replay requirements:
- **Synchronization**: after every action — wait `session.Busy == false`, drain intermediate roundtrips, detect screen change (tcode/screen no./title/modal stack), configurable settle. **Zero blind sleeps.**
- **Popup discipline**: any unexpected `wnd[n]` triggers the registered-handler chain (information popups, multi-logon, "data will be lost", F4 helps, spool dialogs) before failing; every handling recorded.
- Every action returns: success, statusbar deltas, screen-change info, elapsed ms, optional before/after screenshots.
- Production guardrail: agent refuses sessions whose `SystemName` isn't on the config allowlist.

---

## 6. EXECUTION ENGINE (Python core)

- Deterministic interpreter of TestCases: resolves bindings (literal, TestSheet column, Buffer, expression, synthetic-data token), executes ActionModes per step via `ExecuteAction`/`ExecuteBatch`, applies comparators (equals, contains, regex, numeric-tolerance, date-format, not-empty).
- ActionModes: `Input`, `Verify`, `Buffer`, `WaitOn` (poll condition/timeout), `Select`, `Press`, `Constraint` (row-lookup: "in the row where Material = M-01, set Quantity = 5" — works across scrolled table pages and ALV grids via the §5 ops).
- **Recovery scenarios** at suite/test/step scope: `on E-message matching X → cleanup + retry N`, `on unexpected modal → screenshot + handler chain`, `on session loss → relogon + restart test case`. All recovery events in results.
- Parallelism: multiple sessions per box (agent manages one STA thread per session), multi-runner worker protocol pulling from one execution queue.
- Dry-run: full validation (bindings, modules, locator well-formedness) without SAP.
- Evidence per step: screenshots, statusbar capture, elapsed; per test: screenshot strip, created business objects, environment metadata. Reports: HTML + JUnit XML + JSON.

## 7. SELF-HEALING (uses the §4 locator sets)

Ordered locator strategy, engine records which succeeded:
1. Exact scripting Id (fast path).
2. Structural pattern (parameterized volatile indices).
3. **Semantic locator**: score current-screen candidates (from a delta `ScanScreen`) against the stored fingerprint — weighted similarity over type, tech field name, label (embedding similarity via local FAISS/sqlite-vss), tab/screen context, relative position — via `ResolveLocator`.
4. **LLM adjudication** (opt-in, last resort): compact serialized screen tree + intended fingerprint → best candidate + confidence + rationale.
Healed steps pass as "passed (healed)" and open a **healing proposal**; approval updates the module (new version). Nightly **drift scan** opens each modeled screen and reports attribute-level match scores before tests fail.

## 8. AI SERVICES (Python; each = versioned prompt template + service class + golden-file evals)

1. **NL test authoring**: NL request → vector-search candidate modules → LLM composes draft TestCase referencing only existing attributes (JSON-schema enforced; hallucinated ids rejected and re-prompted with validation errors). Human approves.
2. **NL-to-model**: process description/BPMN text → draft `BusinessProcessModel`.
3. **Scan enrichment** (§4.2).
4. **Failure triage**: step context + statusbar history + healing attempts + screenshot (vision) → root-cause class {locator break, test-data issue, environment/auth, app defect, timing} + next action + defect draft; cluster similar failures per run.
5. **Risk-based selection**: requirements/risk weights + changed tcodes/usage exports + failure history → explainable ranked execution list under a time budget (scoring is deterministic; LLM writes the justification only).
6. **Test data synthesis**: valid-shaped values from attribute domains; lookup helpers to find usable master data.
Provider-agnostic `LLMClient` (Anthropic/OpenAI/local stub), temperature 0–0.2, schema-validated outputs, token/cost logging, response caching, redaction layer (structure kept, values stripped) before any external call, "no external LLM" mode degrading to heuristics.

## 9. MODELING, TEST DESIGN, DATA (as previously specified, unchanged in intent)

- `BusinessProcessModel` graph (screens=nodes, actions=edges, decisions, loops, reusable sub-models); path generation (all-edges, all-simple-paths ≤ k, risk-weighted) compiling to TestCase skeletons; pairwise (IPOG/`allpairspy`) + boundary + equivalence-class generation into TestSheets; negative tests asserting expected E-messages; deterministic regeneration lineage.
- TestSheets UI grid, XLSX/CSV import/export, typed columns, row tags; data states/reservation, per-environment pools; buffers persisting across chained test cases (VA01 → VL01N → VF01); credential-store integration, sensitive masking.

## 10. ACCEPTANCE WORKFLOWS (all must work end-to-end)

**W1 — Universal scan, complex screen**: `smt scan --tcode ME21N --deep-tabs` captures header/item ALV grid (all columns), item-detail tabstrip (every tab deep-scanned), document-overview **tree**, toolbar, menus — zero `unmapped` components on this screen; module drafts reviewed and approved.
**W2 — Complex replay**: a test case that in ME21N selects a tree node, sets ALV cells by column-id in specific rows, presses an ALV toolbar button, handles the resulting modal, switches item tabs, saves, and buffers the PO number from the statusbar pattern registry.
**W3 — NL authoring**: VA01 order via natural language → draft → bind qty to TestSheet → run → order number buffered and reported.
**W4 — Chain + recovery**: VA01 → VL01N → VF01 via buffers; injected failure triggers retry then triaged failure with screenshot.
**W5 — Self-healing**: stale locator heals via semantic match → "passed (healed)" → proposal approved → module version bump.
**W6 — MBT generation**: VA01 domains → pairwise → 6–8 instances incl. one negative → executed.
**W7 — Risk-based CI run**: `smt select --budget 30min --changed-tcodes VA01,VA02` → ranked list + justifications → Windows CI agent executes, publishes JUnit/HTML.

## 11. NON-FUNCTIONAL REQUIREMENTS

- Reliability: condition-based waits only; flaky-test quarantine with auto-suggestion.
- Coverage honesty: any component the agent cannot fully drive is surfaced as `unsupported`/`fragile` in scan + results — never a silent skip.
- Auditability: every AI proposal reviewable, versioned, attributable; reports distinguish AI-assisted outcomes.
- Security: redaction before LLM calls; no plaintext credentials; prod-system hard block.
- Performance: <150 ms framework overhead per step (excl. SAP + network); scan targets per §4.1.
- Extensibility: plugin points for ActionModes, popup handlers, data providers; the gRPC contract is the seam for the future Fiori/Playwright agent.
- Quality: agent — xUnit, COM behind interfaces; core — pytest ≥80% on engine/repository/scanner via `FakeUiAgent` fixtures; mypy clean, ruff-formatted; recorded-fixture library covering every §5 matrix row.

## 12. DELIVERY PLAN (each milestone independently demo-able)

1. **M1 — Contract + Agent skeleton**: `uiadapter.proto`, codegen, .NET agent with sessions, ScanScreen (dynpro controls), ExecuteAction (text/select/action families), statusbar events, screenshots, guardrail; Python gRPC client + `FakeUiAgent`. Demo: scripted VA01 from a YAML step list through the agent.
2. **M2 — Universal components**: full §5 matrix — TableControl scroll math, GridView, Trees, TextEdit, menus, VKeys, popup handler chain, delta scans. Demo: W2 replay on ME21N.
3. **M3 — Repository + Scanner + enrichment + review UI**: Demo: W1.
4. **M4 — Engine + buffers + recovery + reporting**: Demo: W4.
5. **M5 — Self-healing + rescan/merge + drift scan**: Demo: W5.
6. **M6 — MBT + data design**: Demo: W6.
7. **M7 — AI authoring + triage + risk selection + dashboards**: Demos: W3, W7.

Per milestone deliver: working code, tests, `docs/` page with architecture notes + runnable example, updated README quickstart.

## 13. WORKING AGREEMENTS FOR YOU (the code builder)

- Ask at most 3 clarifying questions up front; otherwise proceed with these defaults and record assumptions in `docs/assumptions.md`.
- Never invent SAP GUI Scripting API members. The `GuiGridView`/`GuiTree`/`GuiShell` APIs have many easily-misremembered method names — when unsure, isolate behind the agent's component handler, mark `// VERIFY-ON-TARGET`, and add a targeted integration test to run on a real SAP system.
- Typed protobuf all the way; no stringly-typed component payloads.
- Boring, testable code; AI lives in services, not sprinkled through the core.
- After each milestone output: what was built, how to run the demo, known gaps, exact commands for that milestone's acceptance workflow.

Begin with Milestone M1. First present `uiadapter.proto` in full plus the C# component-handler interface hierarchy (signatures + docstrings) for review, then implement.
