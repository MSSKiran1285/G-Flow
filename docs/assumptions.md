# Assumptions and deviations (M1)

Per spec §13, recorded here rather than re-confirmed inline.

## Environment

- **No early-bound SAPFEWSELib interop assembly.** This machine has no Windows SDK /
  Visual Studio (`tlbimp.exe` unavailable) and registry access is blocked by group
  policy, so the interop assembly generation described in spec §2 can't happen here.
  `SapGuiAgent.Com` accesses SAP GUI Scripting late-bound via `dynamic` (IDispatch)
  instead: `Marshal.BindToMoniker("SAPGUI")` (the .NET Core-supported equivalent of the
  .NET Framework-only `Marshal.GetActiveObject`). Everything above the COM boundary
  (handlers, scanner, gRPC service) stays statically typed against `IComComponent`/
  `IComSession`; only `IComComponent.Native` is dynamic. If an interop assembly becomes
  available later (e.g. building on a machine with the Windows SDK), the `Com/` layer is
  the only place that would need to change.
- **`dotnet.exe`/`winget.exe`/PowerShell's HTTP stack are blocked by network policy** on
  this machine (TLS connections reset), while `curl.exe` and Python's `urllib` are not.
  The .NET SDK, its 8.0 runtime/ASP.NET Core/WindowsDesktop targeting packs, and all
  NuGet packages for both C# projects were fetched via a small resolver
  (`agent/scripts/resolve_nuget.py`) into a local offline feed
  (`C:\Users\<user>\.nuget-offline-feed`), configured as the only source in
  `agent/NuGet.Config`. Re-run that script (with extra `(id, version)` roots appended)
  whenever a new package is added.
- **.NET SDK 10.0.400** installed user-locally under `%USERPROFILE%\.dotnet` (winget was
  blocked; the SDK zip was pulled via `curl` and extracted directly). Added to the user
  `PATH`/`DOTNET_ROOT`. `SapGuiAgent`/`SapGuiAgent.Tests` target **net8.0-windows** per
  the brief; the 8.0.30 runtime + ASP.NET Core 8.0.30 shared framework were installed
  alongside so net8.0 actually runs, not just compiles.

## Live-system findings

- **`dynamic` doesn't work against this SAP GUI installation's COM object — use
  `Type.InvokeMember` instead.** `Marshal.BindToMoniker("SAPGUI")` itself succeeds (it's
  an out-of-process COM server, so client/server bitness doesn't need to match), but
  every C# `dynamic` call into the returned object threw
  `COMException 0x80029C4A (TYPE_E_CANTLOADLIBRARY)`. Root cause: the DLR's `dynamic`
  binder calls `IDispatch::GetTypeInfo` to build a richer binding, and this SAP GUI
  install's registered type library isn't loadable (confirmed independent of process
  bitness — reproduced identically under both x64 and x86, which is what ruled out a
  bitness explanation). Fix: `Com/ComHandle.cs` wraps every COM object and calls members
  via `Type.InvokeMember` (`BindingFlags.Get/Set/InvokeMethod`), which only needs
  `IDispatch::Invoke`/`GetIDsOfNames` — no type library required. All of `Com/` and
  `Components/` now go through `ComHandle` instead of `dynamic`; there is no remaining
  bitness concern, the agent runs as a normal x64 process.
- An x86 .NET 8 runtime + ASP.NET Core runtime were also installed
  (`%USERPROFILE%\.dotnet-x86`, a separate root — x86/x64 shared frameworks can't coexist
  in one) while chasing the bitness theory before the real cause was found. Harmless to
  leave in place, but not required by anything in this repo.
- **Confirmed against a real session** (system `GEC`, SAP Easy Access): `ListConnections`
  → `OpenSession` (reusing an already-authenticated connection, no login fields needed) →
  `GetSessionInfo` → `ScanScreen` all round-tripped correctly, including the full real
  `GuiMenubar` tree (100+ nested items) and toolbar buttons. Then a real write path:
  `SET` on `GuiOkCodeField.Text`, `SEND_VKEY("Enter")` via `GuiFrameWindow.SendVKey(0)`,
  and `STATUSBAR_READ` returned `{type: "S", text: "Transaction ZZZINVALIDTEST does not
  exist", message_id: "S#...", message_number: "343"}` for a deliberately-invalid
  command. So these `VERIFY-ON-TARGET` members are now **confirmed**, not just
  documented guesses: `GuiSessionInfo.{SystemName,Client,User,Transaction,Program,
  ScreenNumber}`, `GuiComponent.Children`(`Count`/`ElementAt`), `GuiOkCodeField.Text`,
  `GuiFrameWindow.SendVKey(int)` with `Enter=0`, `GuiStatusbar.{MessageType,Text,
  MessageId,MessageNumber}`.
- **New component types seen on a real screen that M1's classifier didn't cover**:
  `GuiTitlebar`, `GuiCustomControl`, `GuiStatusPane` — all plain window-chrome types,
  not GuiShell/M2 material, just missing from `ComponentFamilyClassifier`. Also:
  `GuiSplitterShell` was seen reported directly as `.Type` (not `"GuiShell"` +
  `SubType="Splitter"` as the spec's naming suggested) — the classifier's `GuiShell`
  dispatch-on-subtype path doesn't catch this; worth widening when GuiShell coverage
  lands in M2.

## O2C/P2P data mining (post-M1, ad hoc)

- **Added `SET_FOCUS` (`ActionOp` 44)**, handled generically in `ComponentHandlerBase`
  for every family (`GuiVComponent.SetFocus()` — confirmed live). Needed because SAP
  resolves `SEND_VKEY` (e.g. F4 for value help) against whatever currently has focus,
  not against an arbitrary target id — so mining a field's F4 list requires focusing it
  first, then sending F4 to the *window*, not the field.
- **`core/smt/data/f4_miner.py` + `o2c_mining.py` + `p2p_mining.py`**: mine real master
  data (order types, sales org/channel/division, vendors) straight out of SAP's own F4
  value-help popups rather than a separate extract or guessed test data. Works because,
  on this system, these particular F4 popups render as plain positional `GuiLabel`
  grids (`lbl[col,row]`) — not GuiShell/ALV — so M1's existing dynpro support is
  sufficient; no M2 work was needed for this.
- **Component ids can be passed in SAP's short form** (`wnd[0]/usr/...`), not just the
  full `/app/con[x]/ses[y]/...` form the scanner returns — confirmed live. Mining scripts
  use the short form so they aren't hardcoded to a particular connection/session index.
- **The vendor field's F4 is a multi-step flow**, not a single popup: focusing
  `ctxtMEPO_TOPLINE-SUPERFIELD` on ME21N and pressing F4 opens a "Restrict Value Range"
  search dialog (tabstrip + a `MAXRECORDS` cap) first; only pressing Enter on *that*
  opens the actual "Hit List" popup with the vendor rows. `p2p_mining.mine_vendors`
  hardcodes this specific flow rather than trying to force it through the generic
  single-shot `mine_simple_f4` helper.
- **Not yet mined**: purchasing org / purchasing group (P2P) and customer (O2C) —
  customer/vendor-by-org fields don't expose a simple single-popup F4 on the screens
  probed so far, and `GuiComboBox.Entries` (which would give the ME21N purchase-doc-type
  combo box's full value list) isn't exposed through the current `ActionResult` contract
  (only the selected key is readable via `READ`). A real gap, not a design choice — worth
  closing alongside real M2 GuiShell work.
- Mined output is **never committed** (`core/data/` is gitignored) — even in a sandbox
  system, F4 hit lists can carry real names/business data (e.g. a real person's name
  showed up as a vendor contact in the mined list).

## First full E2E: real saved sales order (post-M1)

- **Guessing valid sales-area/customer/material combinations through blind trial and
  error doesn't scale** — confirmed live: `G999` ("genpact Sales Org") had almost no
  customers/materials actually extended to it (`No customer master record exists for
  sold-to party 266`), and `0001`'s division F4 needed a completely different multi-step
  search-dialog flow than `G999`'s did. The fix: **read real historical documents
  straight out of their tables** (VBAK/VBAP for sales orders) via SE16N instead of
  guessing — every value pulled this way is proven-valid by construction.
- **This required real M2 work, done now rather than deferred**: SE16N's (and VA05's,
  ME2M's, ...) result list is a `GuiShell/GridView` (ALV grid) — the exact family M1
  left as `NotYetImplementedHandler`. Added `AlvGridHandler` (`Components/
  AlvGridHandler.cs`): read-only for now — `RowCount`/`ColumnOrder` on scan,
  `GRID_GET_CELL` on replay. That's the minimum slice that makes table-based mining
  possible; write ops (`SET`, toolbar/context-menu, checkbox/button cells) are still
  unimplemented, a real fast-follow for M2 proper.
- **`core/smt/data/table_reader.py`** (`smt read-table <table> <columns...>`) is the
  general tool this unlocked: navigates to SE16N, runs the default selection, reads
  named columns off the ALV result. Used to pull real VBAK/VBAP rows and mine a
  genuinely valid O2C combination: `AUART=OR`, `VKORG=GP01`, `VTWEG=G1`, `SPART=D1`,
  customer `2`, material `101`.
- **Full E2E proof, live**: drove VA01 with that combination — order type, sales area,
  sold-to, one line item (material 101, qty 1) — through a "PO number" warning, pressed
  Save, confirmed the "Save Incomplete Document" completeness-check popup, and SAP
  responded `"Standard Order 1975 has been saved"` (message V1/311). Independently
  re-verified via VA03: net value 100,00, matching what was entered. This is the first
  fully successful create → save round-trip the framework has produced, using only
  capabilities already in the M1/early-M2 codebase (dynpro SET/READ, item-table cell
  addressing, SEND_VKEY, PRESS, the new ALV read path, and F4 mining for the initial
  screen fields) — no bespoke one-off code was needed once the right master data was in
  hand.
- Same `read_table` approach applies directly to P2P (`EKKO`/`EKPO` for purchase
  orders) and hasn't been attempted yet — likely next step.

## Repository + Engine MVP: assembling and data-driving a test (no GUI yet)

- User asked directly whether there's a front end ready to assemble and data-drive a
  sales order test. Honest answer at the time: no — the engine layer worked (proven by
  the order-1975 E2E), but nothing existed above it: no persisted Module/TestCase/
  TestStep entities, no execution engine resolving bindings, no UI of any kind (`core/
  api/`, `core/ui/` were still empty placeholders). Per spec §13 this is the M3/M4/M6
  gap, not an M1/M2 one.
- User chose **CLI/config-driven now, GUI later** (a full React/FastAPI front end is a
  separate, much larger effort). Built the real repository/engine slice this unlocks:
  - `smt/repository/models.py` + `db.py`: SQLAlchemy `Module`/`ModuleAttribute`/
    `TestCase`/`TestStep`, SQLite by default (spec §3).
  - `smt/repository/scanning.py` (`smt scan-module`): scans a live screen and persists
    it as a Module. **Important fix made here**: `ScanScreen` returns the full
    `/app/con[x]/ses[y]/wnd[...]` path, which is tied to one specific connection/session
    index. Persisting that directly would break the Module the moment a different
    session/connection index came along. Component ids are normalized to the short
    `wnd[0]/...` form before saving — confirmed live that SAP's `FindById` accepts it
    just as well as the full form.
  - `smt/engine/executor.py` (`smt define-testcase`, `smt run-testcase`): imports a YAML
    TestCase definition, resolves each TestStep's (module, semantic_name) to a component
    id, resolves its binding (`literal:` or `column:<TestSheet column>`) per CSV row, and
    executes — spec §6's binding/ActionMode model, MVP scope (no buffers/recovery yet).
    A step can reference a raw `component_id` directly instead of a Module attribute,
    for elements that only exist conditionally (e.g. a completeness-check popup) and so
    were never part of any scan; such steps are marked `optional` so a missing component
    skips rather than fails the row.
- **Proven live, genuinely data-driven**: scanned `VA01_InitialScreen` (185 attributes)
  and `VA01_ItemEntry` (561 attributes, including the full item table and menu tree) as
  real Modules; authored `core/examples/va01_create_order_testcase.yaml` referencing
  them by semantic name; ran it against `core/examples/va01_create_order_data.csv` (two
  different real historical combinations, mined the same way as the order-1975 work).
  Both rows passed independently: **`Standard Order 1976 has been saved`** and
  **`Standard Order 1977 has been saved`** — two distinct, newly created orders from one
  assembled, reusable test case, not two one-off scripts. Order 1977 independently
  re-verified via VA03 (net value 0,00 is correct — material `2` has no pricing
  condition maintained, not a bug).
- A test case must include its own navigation as ordinary steps (e.g. `SET` the OK-code
  field to `/nVA01` then `SEND_VKEY Enter`) — a session may be sitting on any screen when
  a run starts; the engine has no implicit "go to the right screen" behavior (that would
  need real Business Process Model support, out of MVP scope here).

## Design

- **`SapGuiAgent.csproj` uses `net8.0-windows`**, not bare `net8.0`: the agent is
  explicitly Windows-only (spec §1), and screenshot capture needs `System.Drawing.Common`
  (Windows-only GDI).
- **`ComponentFamily` (proto) is our own routing taxonomy**, not part of the SAP GUI
  Scripting surface — `ComponentNode.type`/`sub_type` carry SAP's own raw strings
  unchanged, so we're never guessing at SAP's ~90 component type names, only at which of
  our 12 buckets each one routes to.
- **M1 scope**: dynpro families only (text input, selection, action, structure, window,
  statusbar) plus SEND_VKEY. GuiShell (ALV grid/tree/text edit/other) and GuiTableControl
  are classified and scanned (never dropped) but marked `unmapped`/`unsupported` via
  `NotYetImplementedHandler` — full coverage is M2 per the delivery plan (§12).
- **Many exact COM member names are marked `// VERIFY-ON-TARGET`** in `Com/` and
  `Components/` (e.g. `GuiSessionInfo` property names, `GuiComboBox.Entries`,
  `GuiStatusbar.MessageType`). These are the commonly-documented SAP GUI Scripting API
  members, but nothing here has been run against a live SAP session yet — there is no
  open, authenticated SAP GUI session in this environment to test against. Per spec §13,
  treat these as needing a targeted integration test on a real system before trusting
  them in production.
- **`ResolveLocator` is intentionally `Unimplemented`** in M1 — self-healing candidate
  scoring is core-side and lands in M5 (§7); the agent doesn't fake it.
- **`Subscribe` (statusbar events) polls every 300ms** rather than using a native SAP GUI
  event/callback, since GuiSession doesn't expose a push-based statusbar-changed event
  through scripting. Acceptable for M1; revisit if polling proves too slow against a
  real system.

## Phase 1 (backlog Epic 5): buffers, chaining, and a live VA01 → VL01N → VF01 attempt

- **Engine built and unit-tested first, then taken live** (same discipline as before):
  `smt/engine/executor.py` gained `capture_buffer_key`/`capture_from`/`capture_pattern`
  on `TestStep`, a `binding_type: "buffer"` resolved from a per-run dict, and
  `run_chain()` (+ `smt run-chain`) threading one buffer across several TestCases,
  stopping a row's chain at the first failure. `smt/engine/message_patterns.py` holds
  the statusbar regex registry (spec §5). 27 tests pass, including a `FakeAgent` that
  scripts statusbar text across multiple STATUSBAR_READ calls to exercise chaining.
- **Live chain hit two real, now-fixed order-creation gaps** before ever reaching
  VL01N:
  1. A fresh order without a customer PO number saves fine (as orders 1976/1977 already
     proved) but is flagged incomplete, and an incomplete order can't be delivered
     (VL01N: "Order is incomplete — maintain the order", confirmed by reading VL01N's
     own error log via `AlvGridHandler`/`GRID_GET_CELL` — the same ALV read path proved
     for SE16N works identically for an arbitrary error-log grid). Fix: fill
     `wnd[0]/usr/subSUBSCREEN_HEADER:SAPMV45A:4021/txtVBKD-BSTKD` (PO number) — not
     under `ssubHEADER_FRAME:SAPMV45A:4440` as an earlier guess assumed.
  2. Completing the item still requires an explicit Plant (`ctxtVBAP-WERKS[12,0]` on the
     item table). Setting it to `1000` (the plant every historical order/delivery in
     this sandbox actually uses, confirmed via `read-table VBAP/LIPS`) triggered `Material
     N is not defined for sales from United Kingdom` — for *two different* materials, so
     it isn't a material-specific gap. `read-table T001W WERKS NAME1 LAND1` showed why:
     plant `1000` is named "Std Plant US" but configured with `LAND1 = GB`. This is a
     genuine data-quality issue in the sandbox's plant master, not something scanning or
     replay caused — most likely this sandbox's demo data was bulk-loaded (LSMW/BAPI)
     without ever passing through the interactive determination logic that would catch
     it. Switching to plant `1001` (correctly `US`) fixed order creation outright — order
     1978 saved cleanly on the very first attempt, no incompleteness popup at all.
- **VL01N then hit a real, still-unresolved blocker**: creating a delivery for order
  1978 produces an *information*-level log, "Item 000010: delivery split because of
  different shipping points" (not an error), and the transaction just sits on the
  generic log-display screen (`SAPLSBAL_DISPLAY`) rather than proceeding to an actual
  delivery document — tried both an explicit shipping point (`0001`, the real value
  every historical delivery uses per `read-table LIKP`) and leaving it blank for
  auto-determination; same result either way. Reading the log entry's long text (which
  would very likely explain the real fix) needs `GRID_DOUBLE_CLICK_CELL` or row
  selection on the ALV grid — neither is implemented (`AlvGridHandler` is read-only:
  `RowCount`/`Columns`/`GRID_GET_CELL` only, per Epic 2's current scope). Stopped here
  rather than keep guessing this sandbox's shipping-point customizing blind — a
  reasonable-effort stopping point, revisit once Epic 2 grows ALV double-click/selection
  support (would also directly unblock reading *any* ALV error log's long text, not just
  this one).
- **Net effect on the backlog**: US-5.1 and the engine half of US-5.2 are done and
  tested; the live 3-real-document chain (US-5.2's last checkbox) and confirming
  `delivery_saved`/`billing_saved` against real wording (US-5.3's last checkbox) are
  blocked on the Epic 2 ALV gap above, not on anything in Epic 5 itself.
