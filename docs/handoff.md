# Handoff: Script-builder web UI for SapModelTest

**Date:** 2026-09-06
**Repo:** `c:\Users\703393028\G-Flow` (git, branch `main`)
**Read this whole file before touching anything.** It exists so a fresh conversation
can pick up exactly where this one left off, without re-deriving context or
re-discovering bugs that are already fixed.

## What this project is

SapModelTest (repo folder name `G-Flow`) is a SAP GUI test-automation tool:

- **`agent/SapGuiAgent`** — a C# gRPC service that drives a real, live SAP GUI
  session via SAP GUI Scripting (late-bound COM, see `agent/SapGuiAgent/Com/ComHandle.cs`).
  This is the only thing that actually touches SAP.
- **`core/smt`** — Python: a repository (SQLite via SQLAlchemy) of scanned `Module`s
  (screens) and `TestCase`s (ordered steps against a Module's attributes), a
  deterministic execution engine, and a FastAPI app (`core/smt/api/`) exposing all
  of it over HTTP.
- **`core/ui`** — React + TypeScript + Vite frontend (the "script-builder UI"),
  talking to the FastAPI backend, proxied through the Vite dev server.
- **`docs/assumptions.md`** — the project's running log of live-verified findings,
  gotchas, and "VERIFY-ON-TARGET" corrections. **Read this file's most recent
  entries (bottom of file) for full technical detail on everything summarized
  below** — this handoff is a map, `assumptions.md` has the actual prose.
- **`docs/backlog.md`** — feature backlog / epics.
- **`docs/o2c-config-fixes.md`** — the O2C (Order-to-Cash) chain's config/master-data
  fix record; O2C (VA01 → VL01N → VF01) was proven end-to-end in an earlier session
  and is not part of this handoff's open work.

**Reference-only sibling project:** `c:\Users\703393028\G-Stride` — visual/UX
inspiration for the UI only. **Never modify it.**

## How to run everything

Three separate processes, in this order:

1. **C# agent** (needs a real SAP Logon already open with an active connection):
   ```
   cd agent && dotnet run --project SapGuiAgent
   ```
   Listens on `localhost:50051`.
   ⚠️ **Launch this via Bash `nohup`, not PowerShell `Start-Process`** — see
   "Gotchas" below; PowerShell-launched background processes have been
   intermittently reaped between tool calls this session.
   ```bash
   cd agent && nohup ./SapGuiAgent/bin/Debug/net8.0-windows/SapGuiAgent.exe > /tmp/sapagent.log 2>&1 &
   ```
   (First build with `dotnet build` from a PowerShell call with
   `$env:DOTNET_ROOT`/`$env:PATH` set — see any recent commit message for the
   exact incantation — then launch the built `.exe` directly via bash nohup.)

2. **FastAPI backend** (from the **repo root**, not `core/` — `DEFAULT_DB_PATH` is
   relative to repo root):
   ```bash
   cd "c:\Users\703393028\G-Flow" && nohup core/.venv/Scripts/python -m smt.cli.main run-api --target localhost:50051 --port 8000 > /tmp/fastapi.log 2>&1 &
   ```
   Listens on `127.0.0.1:8000`. Check health: `curl -s http://127.0.0.1:8000/api/connections`
   — first request right after startup sometimes transiently fails (gRPC channel
   still warming up); retry once before concluding it's actually down.

3. **React dev server**:
   ```bash
   cd core/ui && npm run dev
   ```
   Listens on `127.0.0.1:5173` — **this is the actual UI**, proxying `/api` calls to
   `:8000`. `http://127.0.0.1:8000` alone has no page of its own (only `/api/...`
   and Swagger at `/docs`) — a user hit this exact confusion this session.

**Both C# and Python code changes require restarting their respective process** (no
hot-reload). Frontend has Vite HMR — usually no restart needed, `npm run build`
is still worth running once to confirm no TS errors.

**Every C# rebuild needs `SapGuiAgent.exe` stopped first** (file lock):
```powershell
Get-CimInstance Win32_Process -Filter "Name='SapGuiAgent.exe'" | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }
```

## What's been built this session (chronological)

Starting point: O2C chain already proven; user asked to build a script-builder
web UI (FastAPI + React) and then use it to build the **P2P scenario** — that
second half (P2P) **has not been started yet**, see "What's next" below.

1. **FastAPI + React script-builder UI, v1** (commits `4b2495b`, `237e2ca`,
   `90505cc`) — Modules browse/scan, Scripts (TestCase) editor, Chains builder,
   run results. First cut of Module scanning did a whole-screen scan and
   persisted everything; corrected on feedback to a curated pick-and-choose flow
   (scan-preview → save selected attributes only).

2. **Live Ctrl+Click element picker** (commit `394bc15`) — replaced whole-screen
   scanning with the real desired interaction: launch the transaction, then
   Ctrl+Click individual fields/controls directly in the live SAP GUI window,
   one at a time, until "Stop scanning". New gRPC streaming RPC
   `StartElementPicker` (`proto/uiadapter.proto`); C# Win32 polling
   (`agent/SapGuiAgent/Native/PointerWatch.cs`, `ClickEdgeDetector.cs`) detects a
   real OS-level Ctrl+Click; `ComponentHitTester.cs` hit-tests the click point
   against a fresh scan. FastAPI relays the stream to the browser via REST
   polling (`core/smt/api/capture.py`).

3. **English caption capture** (commits `0eca29a`, `97e158e`) — added
   `PickedComponent.caption`/`ModuleAttribute.caption` end to end. Needed **four**
   heuristics, discovered only by testing live (`ComponentHitTester.cs` C# side,
   `scanning.py` Python side — kept in sync, same order):
   1. **Id-based sibling** (`FindCaptionById`/`_caption_by_id`): `ctxtVBAK-AUART` ↔
      `lblVBAK-AUART` (same suffix, `lbl` prefix).
   2. **Positional fallback** (`FindCaptionByPosition`/`_caption_by_position`):
      nearest caption-like control (label, or non-editable text field) on the same
      row, strictly to the left — needed because VA01's "Order Type" caption for
      `VBAK-AUART` is actually rendered by an unrelated control,
      `txtRV45A-TXT_AUART`, with no naming relationship at all.
   3. **Self-captioned controls** (buttons/tabs/radio buttons/checkboxes/menu
      entries): their own `.Text`/`.Tooltip` already *is* the caption — a button
      reading "Save" doesn't need to search anywhere else.
   4. **Table-column lookup** (`FindCaptionByColumn`/`_caption_by_column`): a
      classic `GuiTableControl` cell's column header sits above every data row,
      not aligned with any one of them, so neither heuristic above can find it.
      New `TableControlHandler.cs` (agent) populates `ComponentNode.table_detail`
      from `GuiTableControl.Columns` at scan time (finally wiring up proto
      messages — `TableControlDetail`/`TableColumn` — that had existed unused
      since early in the project). Live-verified across all 17 rows of VA01's
      item table: `VBAP-POSNR`→"Item", `RV45A-MABNR`→"Material Number",
      `RV45A-KWMENG`→"Order Quantity".

4. **Highlight-on-screen action** (commit `97e158e`, generalized in `292e574`) —
   new `HIGHLIGHT` op in `ActionOp`, handled universally in
   `ComponentHandlerBase.cs` (like `SET_FOCUS`) via `GuiVComponent.Visualize(true)`
   — draws a colored border around a component on the real live screen. Two
   endpoints: `POST /modules/capture/{id}/highlight` (reuses an active capture
   session's handle — fast, but only works while "Capturing…" is open) and the
   more generally useful `POST /modules/highlight` (opens/closes its own
   short-lived session — works from the review step and from
   `ModuleDetailView`, i.e. any saved Module, which have no active capture
   session to reuse). Buttons wired into `ScanModuleDialog.tsx` (capturing +
   review steps) and `ModuleDetailView.tsx`.
   - **UX bug fixed just before this handoff (uncommitted — see "Uncommitted
     changes" below):** the highlight button was there all along but styled with
     the `.drag-handle` CSS class (grab cursor, no hover feedback), so it read as
     a decorative icon, not a clickable button — user couldn't find it despite it
     being visible in a screenshot. Added a proper `.icon-btn` class (pointer
     cursor, visible hover background) in `core/ui/src/styles/base.css` and
     switched the highlight (and adjacent remove/trash) buttons to it.

5. **Performance fix** (commit `85db191`) — `StartElementPicker` was doing a full
   `root_id="*"` rescan of the *entire* screen on every single click. Confirmed
   live that a data-heavy screen (VA01's item overview table) takes 20-30s to
   scan (hundreds of cells × ~11 late-bound COM property reads each) — this made
   multi-click capture sessions unusable, per direct user feedback ("pick and
   choose is extremely slow"). Fixed by caching the snapshot across clicks in
   `UiAgentService.cs`, only refreshing when a cheap `GuiSessionInfo` check
   (tcode/screen/window-count/modal-titles — no tree walk, see
   `SapGuiComSession.CaptureContext()`) shows the screen actually changed.
   **Known tradeoff, not yet addressed:** scrolling a table without changing
   screen/tcode goes undetected between clicks — a click after a scroll can
   hit-test against stale row positions.

6. **Window-title grouping** (commit `85db191`) — added `window_title` (the real
   on-screen title of the window/dialog a field lives in, via
   `GuiMainWindow.Text`/`GuiModalWindow.Text`) alongside every
   captured/scanned/saved component. `ComponentHitTester.FindWindowTitle` (C#,
   picker path) / a window-title index built in `scan_screen_preview` (Python,
   whole-screen path). Persisted on `ModuleAttribute` (**DB schema changed** —
   see "DB note" below). `ScanModuleDialog`'s capturing/review tables and
   `ModuleDetailView` now render a header row per distinct window (e.g. "Create
   Sales Order: Initial Screen") before its fields, exactly matching what the
   user asked for.

7. **A serious, foundational bug found and fixed** (commit `292e574`) — user
   reported "when I click stop scanning, it tries to exit SAP screen." Root
   cause: `SapGuiConnectionManager.CloseSessionAsync` called `wnd[0].Close()` on
   **every** `close_session` call — and `close_session` is called after *every*
   scan, capture, mining script, and every single data row of every test run
   (`executor.py`'s `_run_one_row`), always against the same real,
   already-open session (`open_session(connection_id=...)` attaches to
   whatever's already there; `GuiSession.Id` is the real session id, not a
   synthetic per-request one — so all callers share the same underlying
   window). **This is almost certainly the real explanation for the repeated
   stacked "Log Off" confirmation dialogs seen throughout this whole project's
   testing history** (this session and probably earlier ones too) — not
   primarily the OS-input/cursor theory floated earlier in this session (see
   below), which was a real, separate, but much smaller-impact finding. Fixed by
   simply removing the `.Close()` call — closing a session now only releases the
   server's own STA-thread bookkeeping, leaving the real SAP window exactly as
   the user left it. Live-verified: start/stop a capture session, confirmed via
   a fresh scan the session stayed on the exact same screen, no extra windows.

8. **Real table-cell read/write** (commit `292e574`) — user asked "table fields
   are identified as text fields, how will this be resolved during execution?"
   A captured table-cell attribute's `component_id` always encodes one specific
   row (whatever was visible at capture time) — reading/writing it always hits
   that exact row, with no way to address a different row for a different data
   row in a test run. Implemented real `TABLE_GET_CELL`/`TABLE_SET_CELL` in
   `TableControlHandler.ExecuteCoreAsync` via
   `GuiTableControl.GetAbsoluteRow(row).Item(columnIndex)` — column index (not a
   technical name; `GuiTableColumn` has no documented name property) passed via
   the existing `ActionParams.column_id`, stringified, same shape ALV grid ops
   already use (`AlvGridHandler`). Live-verified against the real item overview
   table: wrote "5" to row 0's quantity, "12" to row 1's, read both back
   independently and correctly (row 1's write didn't disturb row 0). **This
   read/write pair is implemented but not yet wired into anything at the
   TestCase/Module level** — see "What's next".

## Uncommitted changes (as of this handoff)

```
M core/ui/src/components/Modules/ModuleDetailView.tsx
M core/ui/src/components/Modules/ScanModuleDialog.tsx
M core/ui/src/styles/base.css
```

This is the `.icon-btn` highlight-button-discoverability fix (item 4's last bullet
above). It's been built (`npm run build` succeeded) but **not yet committed** —
the user only asked "where is the highlight option?", not for a commit. **Commit
this before doing anything else if the user doesn't ask for further changes to
it first** — don't lose it. Suggested commit message angle: "Fix the highlight
button reading as decorative instead of clickable (wrong cursor/no hover state)".

## Current live state (as of this handoff)

- All three processes (agent, FastAPI, Vite) were running and healthy as of the
  last check in this conversation. **A new conversation should re-verify** —
  processes may have been stopped/reaped since (see Gotchas).
- Live SAP session: `VA01`, screen `101` (initial screen) as of the last check —
  **but this could easily have drifted since**; always call
  `GET /api/connections` and a fresh scan before assuming anything about
  current screen state.
- **Inert test data left in the live system, harmless but worth knowing about**:
  during live verification of `TABLE_SET_CELL`, row 0's quantity column was set
  to `"5"` and row 1's to `"12"` on whatever VA01 order was open at the time.
  Nothing was saved (no `PRESS` on the Save button was ever issued), so this is
  just unsaved on-screen state — it'll vanish the moment that order is actually
  saved, cancelled, or the session navigates away. Not a concern, just don't be
  confused if you see "5"/"12" sitting in an item table mid-session.

## Gotchas / hard-won lessons (don't rediscover these)

- **Window position drift**: the live SAP GUI window (class `SAP_FRONTEND_SESSION`)
  repeatedly drifts to negative/off-screen coordinates between actions. Before
  any coordinate-based interaction (OS-level clicks), re-enumerate via
  `EnumWindows`+`GetClassName`+`GetWindowText` (don't trust a cached hwnd — it
  can also change entirely, not just move) and reposition with
  `SetForegroundWindow`+`SetWindowPos`. **Do not** use `saplogon.exe`'s own
  `Process.MainWindowHandle` — wrong window, silently fails.
- **PowerShell `Start-Process` for long-running background processes is
  unreliable in this environment** — `SapGuiAgent.exe` launched this way got
  silently killed between tool calls at least twice this session (likely a Job
  Object "kill on close" reaping child processes when the launching
  tool-invocation's own process tree exits). **Bash `nohup` has been reliable**
  for both `SapGuiAgent.exe` and the FastAPI process — prefer it. PowerShell
  `Start-Process` was still used successfully at least once for the agent this
  session (real click detection did work through it) — but nohup is the safer
  default going forward. If click detection mysteriously stops working, first
  suspect the launch mechanism.
- **`SetCursorPos`/`GetCursorPos` stopped working entirely at one point this
  session** — `SetCursorPos` returned `false`, `GetCursorPos` reported `(0,0)`
  regardless of what was set, confirmed via a bare P/Invoke probe with zero SAP
  involvement. This is an environment/interactive-desktop issue (this
  automation session losing control of the real cursor), not a code bug — it
  blocks OS-level Ctrl+Click simulation specifically. **If you need to
  live-verify anything involving simulated clicks and it silently fails, check
  `GetCursorPos` readback first** before assuming a code regression. Everything
  that doesn't need cursor control (direct `execute_action` calls, `scan_screen`,
  `HIGHLIGHT`, `TABLE_GET_CELL`/`SET_CELL`) is unaffected and was the primary
  verification method used once this was discovered.
- **Stray "Log Off" dialogs**: if you see these stacked up (`wnd[1]`, `wnd[2]`,
  ...), they're very likely gone now that item 7 above is fixed — but if they
  recur, dismiss safely with: scan `root_id="*"`, find the highest-numbered
  `wnd[N]`, press its `btnSPOP-OPTION2` ("No" — decline logoff, preserve
  session), repeat until only `wnd[0]` remains.
- **Every `grpc_tools.protoc` regeneration breaks `uiadapter_pb2_grpc.py`'s
  import** — changes `from . import uiadapter_pb2` to a bare
  `import uiadapter_pb2`, which fails at runtime. Always follow regeneration
  with:
  ```bash
  sed -i 's/^import uiadapter_pb2 as uiadapter__pb2$/from . import uiadapter_pb2 as uiadapter__pb2/' core/smt/adapter/generated/uiadapter_pb2_grpc.py
  ```
  (C# side regenerates automatically on `dotnet build` via the `Protobuf`
  MSBuild item — no manual step needed there.)
- **DB schema changes require deleting `core/data/repository.db`** — no
  migration system exists (`Base.metadata.create_all()` doesn't `ALTER` existing
  tables). It's gitignored and local-only; safe to delete (stop FastAPI first to
  release the file lock) and let it regenerate empty. This happened this session
  when `window_title` was added to `ModuleAttribute` — the DB currently has
  whatever was (re-)scanned/saved since then, likely close to empty again.
- **All `smt` CLI commands run from the repo root**, not `core/` —
  `DEFAULT_DB_PATH = Path("core/data/repository.db")` is only correct relative to
  the repo root. Don't "fix" this to be `core/`-relative; it's been gotten wrong
  and reverted once already.
- **Bash tool JSON/backslash escaping is unreliable for component ids with
  literal backslashes** (e.g. VA01's `tabpT\01` tab-strip id) — when a live test
  needs such an id, write a small `.py` script file with a raw Python string
  literal (`"...\\01..."` or a real backslash) and run it, rather than trying to
  inline it through `curl -d` or a `-c` one-liner. Delete scratch scripts
  afterward (this session used and cleaned up `core/scratch_table_test*.py`,
  `core/scratch_highlight_test.py` — if you see stray `core/scratch_*.py` files,
  they're safe to delete, not tracked work).

## What's next

The user's **original, still-outstanding ask** from the start of the UI-building
work: use the now-working script-builder UI to build the **P2P scenario**
(`ME21N` create PO → `MIGO` goods receipt → `MIRO` invoice verification), reusing
an existing mined vendor from `core/data/p2p_master_data.json` (confirmed scope
decision: no new vendor creation via XK01). This has **not been started** —
everything done this session has been fixing/hardening the UI tooling itself, at
the user's direction, in response to real usage friction they hit while trying to
scan P2P screens.

Known gaps to close *before or during* P2P work:

- **Purchasing org/purchasing group are not yet mined** (per
  `core/smt/data/p2p_mining.py`'s own docstring and `docs/backlog.md`) — they
  live on ME21N's Org. Data sub-tab as plain fields, not yet scanned/mined. Mine
  these live (same discipline as everything else — real values only, never
  guessed) before authoring the ME21N TestCase.
- **`TABLE_GET_CELL`/`TABLE_SET_CELL` are implemented and live-verified at the
  agent level but not yet used by anything at the TestCase/Module level** — no
  UI affordance exists yet for a test step to say "row 2, column MABNR" instead
  of a fixed component_id. This will matter immediately for P2P (ME21N's item
  table, multiple line items) and would have mattered for O2C's item table too.
  Whether to build proper UI support for this now (a `TestStep` needs a way to
  bind a `row` parameter per data row, e.g. from a CSV column) or work around it
  per-scenario is an open design decision — **flag it to the user rather than
  guessing**, since it affects how P2P's item-line steps get authored.
- **Scrolling-during-capture cache staleness** (item 5's tradeoff) — not urgent,
  but worth knowing if a capture session behaves oddly after scrolling a table.
- Housekeeping note already fixed earlier in the project (not this session, but
  relevant to P2P): `message_patterns.py`'s `billing_saved` pattern was
  corrected to `r"Document (\d+) has been saved"`. **New patterns for P2P** (PO
  saved, material document, invoice saved) need adding to that same registry —
  **only once their real statusbar wording is confirmed live**, same discipline,
  never guessed in advance.

## Test status (last confirmed, this session)

- **C# (`agent/SapGuiAgent.Tests`)**: 82 passed, 0 failed
  (`dotnet test` from `agent/`, with `DOTNET_ROOT`/`PATH` set to `$env:USERPROFILE\.dotnet`).
- **Python (`core/tests`)**: 67 passed, 0 failed (`.venv/Scripts/pytest tests -q`
  from `core/`).
- **Frontend**: `npm run build` clean, no TypeScript errors (from `core/ui/`).

Re-run all three before trusting this is still true if picking this up much
later — nothing since the last run should have broken them, but the
uncommitted `.icon-btn` change (see above) was verified via `npm run build`
only, not a fresh full test pass (there's no frontend test suite in this
project — `npm run build` passing is the established smoke check, see the
approved plan in `C:\Users\703393028\.claude\plans\peaceful-fluttering-badger.md`).
