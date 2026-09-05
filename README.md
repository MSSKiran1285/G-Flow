# SapModelTest

AI-first, model-based test automation framework for SAP ECC via SAP GUI. See
[SAP-MBT-Framework-Prompt.md](SAP-MBT-Framework-Prompt.md) for the full spec and
[docs/assumptions.md](docs/assumptions.md) for environment-specific decisions and
everything confirmed (or found broken) against a real system.

## Status

- `proto/uiadapter.proto`: full gRPC contract (session lifecycle, scan, replay,
  self-healing, events, screenshots).
- `agent/` (C# .NET 8 `SapGuiAgent`): dynpro-family scan/replay, statusbar events,
  screenshots, allowlist guardrail, and ALV grid support (`GuiShell/GridView` —
  row/column metadata, cell reads, double-click, row select, current-cell/cursor) plus
  `COORDINATE_CLICK_FALLBACK` — a real OS-level mouse click (Win32) for the rare control
  that doesn't honor the scripting-API equivalent, gated behind `allow_fragile_fallback`
  and always reported `fragile`. COM access goes through `Com/ComHandle.cs`
  (`Type.InvokeMember`), not C#'s `dynamic` keyword — see assumptions doc for why.
  GuiTableControl and ALV write ops are still unimplemented.
- `core/` (Python): `UiAgentPort` seam + real gRPC client + `FakeUiAgent` (fixture
  replay); a SQLite repository (`Module`/`ModuleAttribute`/`TestCase`/`TestStep`) and a
  deterministic execution engine that resolves bindings (literal/column/**buffer**)
  against a CSV TestSheet, with a statusbar message-pattern registry for capturing
  document numbers and `run_chain` for threading a buffer across several TestCases;
  F4-based and table-based (SE16N) master-data mining; a Typer CLI (`smt ...`) tying it
  together.
- **A script-builder web UI now exists**: `core/smt/api/` (FastAPI) exposes the
  repository/engine over HTTP, and `core/ui/` (React + Vite, no component library,
  design tokens inspired by the read-only G-Stride reference project) lets a tester
  browse/scan Modules, build a TestCase's steps visually (add/edit/reorder/duplicate/
  remove — drag-and-drop plus a parallel keyboard reorder path), run it against an
  inline data grid, and chain several TestCases together (mirrors `run_chain`) with
  live pass/fail results and captured buffers shown per step/stage. Verified live
  end-to-end through the real HTTP API against the live SAP session. See "Script
  builder UI" below.
- **Proven fully end-to-end against a live system, order through FI posting**: scanned
  two real screens as Modules, assembled a data-driven TestCase from them (no hardcoded
  component ids), ran it against several different, historically-mined data rows, and
  got back independently verified, real saved sales orders. The buffer/chaining engine
  is built and unit-tested; live chaining then created a real **Outbound Delivery
  (`80001138`)** referencing a real order. Getting there required root-causing a VL01N
  "delivery split" info-log down to a specific wrong shipping-point value (fixed with no
  config change) via `COORDINATE_CLICK_FALLBACK` (a real OS-level click, built
  specifically because no scripting-API gesture could open the log's long text). Post
  Goods Issue then hit a genuine `OBYC` account-determination gap — rather than build a
  new company code/plant to sidestep it, three real customizing gaps (`OBYC` account
  determination, an `FBN1` number-range interval, an `FTXP` tax code) were found and
  fixed live on the existing environment. **Billing (`VF01`) now produces a real FI
  accounting document** (`BKPF` doc `100000017`) — the full O2C chain, order through FI
  posting, is proven. Full narrative in `docs/assumptions.md`; the three fixes in detail
  in `docs/o2c-config-fixes.md`.

## Build & test

**C# agent** (needs the offline NuGet feed set up per `docs/assumptions.md` if
`api.nuget.org` isn't reachable from `dotnet.exe` on your machine):

```
cd agent
dotnet build
dotnet test
dotnet run --project SapGuiAgent   # listens on :50051 (HTTP/2, gRPC only)
```

**Python core**:

```
cd core
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/pytest
```

## Demos

All of these need a running `SapGuiAgent` (`dotnet run --project agent/SapGuiAgent`)
with SAP GUI open and an active connection. Run `smt` commands from the repo root.

**Scripted step list** (offline against a fixture, or live):

```
core/.venv/Scripts/python -m smt.cli.main examples/va01_steps.yaml \
  --fixture core/tests/fixtures/va01_minimal.json
# or: --target localhost:50051
```

**Mine master data via F4 / table reads** (writes to `core/data/`, never committed):

```
smt mine-o2c            # order types, sales org/channel/division via VA01's F4 help
smt mine-p2p            # vendors via ME21N's F4 help
smt read-table VBAK VBELN AUART VKORG VTWEG SPART KUNNR NETWR --max-rows 20
```

**Assemble and data-drive a sales-order-creation test** (the repository + engine MVP):

```
smt scan-module VA01_InitialScreen --tcode VA01
smt scan-module VA01_ItemEntry --tcode VA01 \
  --prefill "wnd[0]/usr/ctxtVBAK-AUART=OR" --prefill "wnd[0]/usr/ctxtVBAK-VKORG=GP01" \
  --prefill "wnd[0]/usr/ctxtVBAK-VTWEG=G1" --prefill "wnd[0]/usr/ctxtVBAK-SPART=D1" \
  --vkey-before-scan Enter

smt define-testcase core/examples/va01_create_order_testcase.yaml
smt run-testcase VA01_CreateStandardOrder --sheet core/examples/va01_create_order_data.csv
```

**Chain several TestCases with a shared buffer** (e.g. an order number created by one
feeding a delivery created by the next):

```
smt run-chain --step "OrderCase:orders.csv" --step "DeliveryCase:deliveries.csv"
```

The CLI/config-driven path above still works unchanged; the same repository/engine is
now also reachable through a web UI (see `docs/assumptions.md` for the original
CLI-first scoping discussion, and below for the UI itself).

## Script builder UI

Three processes, in order (all commands below run from the **repo root**, same as
every `smt` command above):

```
cd agent && dotnet run --project SapGuiAgent        # :50051, needs SAP GUI open+connected

core/.venv/Scripts/python -m smt.cli.main run-api    # :8000

cd core/ui && npm install && npm run dev             # :5173, proxies /api to :8000
```

Open `http://localhost:5173`. **Modules**: browse scanned screens, or scan a new one
live (tcode, optional prefill fields/vkeys to reach a second screen) — the scan is a
two-step *preview then pick*: every field/button/label found is shown grouped by
window (`wnd[0]`, `wnd[1]`, ...) with a checkbox and an editable name per row, and
only the ones actually checked get saved as the Module's attributes, not the whole
screen. **Scripts**:
build a TestCase's steps visually — pick a Module+attribute (or a raw component id
for conditional elements like popups), an action, a binding (literal / from test data
/ captured by an earlier step), reorder via drag-and-drop or the keyboard (arrow keys
on each row's ⠿ handle) — then run it against an inline data grid and see real
pass/fail + statusbar output. **Chains**: sequence several scripts, one data grid per
stage, sharing captured buffers across stages (mirrors `run-chain`).

## Known gaps

- GuiTableControl and ALV *write* ops beyond what's built (toolbar/context-menu,
  checkbox/button cells) — reads, double-click, row-select, and current-cell all exist
  now. Trees, text-edit shells, other shells — all still unimplemented.
- Self-healing (`ResolveLocator`) — not started.
- The script-builder UI is a lean MVP: no Object Repository workspace, no persisted
  Test Data library (data grids are entered inline per run, not saved), no execution
  history/audit vault, no global search. No AI services, no business-process modeling.
- Recovery scenarios (retry/relogon), reporting (HTML/JUnit) — engine MVP doesn't have
  these yet. Buffers + chaining across TestCases exist (`run_chain`); the full O2C
  chain (order → delivery → goods issue → billing → FI posting) is now proven live
  (see Status above).
- Many COM member names are marked `VERIFY-ON-TARGET` in `agent/SapGuiAgent/Com` and
  `Components` — some are now confirmed live (see assumptions doc), most aren't yet.
