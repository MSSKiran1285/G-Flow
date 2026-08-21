# SapModelTest

AI-first, model-based test automation framework for SAP ECC via SAP GUI. See
[SAP-MBT-Framework-Prompt.md](SAP-MBT-Framework-Prompt.md) for the full spec and
[docs/assumptions.md](docs/assumptions.md) for environment-specific decisions and
everything confirmed (or found broken) against a real system.

## Status

- `proto/uiadapter.proto`: full gRPC contract (session lifecycle, scan, replay,
  self-healing, events, screenshots).
- `agent/` (C# .NET 8 `SapGuiAgent`): dynpro-family scan/replay, statusbar events,
  screenshots, allowlist guardrail, and read-only ALV grid support (`GuiShell/GridView`
  — row/column metadata + cell reads). COM access goes through `Com/ComHandle.cs`
  (`Type.InvokeMember`), not C#'s `dynamic` keyword — see assumptions doc for why.
  GuiTableControl and ALV write ops are still unimplemented.
- `core/` (Python): `UiAgentPort` seam + real gRPC client + `FakeUiAgent` (fixture
  replay); a SQLite repository (`Module`/`ModuleAttribute`/`TestCase`/`TestStep`) and a
  deterministic execution engine that resolves bindings against a CSV TestSheet; F4-based
  and table-based (SE16N) master-data mining; a Typer CLI (`smt ...`) tying it together.
- **Proven end-to-end against a live system**: scanned two real screens as Modules,
  assembled a data-driven TestCase from them (no hardcoded component ids), ran it
  against two different, historically-mined data rows, and got back two independently
  verified, real saved sales orders. Full narrative in `docs/assumptions.md`.

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

This is CLI/config-driven, not a graphical front end — no React/FastAPI UI exists yet
(`core/api/`, `core/ui/` are still empty). See `docs/assumptions.md` for that scoping
discussion.

## Known gaps

- GuiTableControl and ALV *write* ops (SET, toolbar/context-menu, checkbox/button
  cells) — read-only ALV support exists, nothing else in the §5 GuiShell matrix does.
  Trees, text-edit shells, other shells — all still unimplemented.
- Self-healing (`ResolveLocator`) — not started.
- No web UI, no FastAPI backend, no AI services, no business-process modeling.
- Recovery scenarios (retry/relogon), buffers across chained test cases, reporting
  (HTML/JUnit) — engine MVP doesn't have these yet.
- Many COM member names are marked `VERIFY-ON-TARGET` in `agent/SapGuiAgent/Com` and
  `Components` — some are now confirmed live (see assumptions doc), most aren't yet.
