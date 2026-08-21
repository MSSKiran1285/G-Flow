# SapModelTest

AI-first, model-based test automation framework for SAP ECC via SAP GUI. See
[SAP-MBT-Framework-Prompt.md](SAP-MBT-Framework-Prompt.md) for the full spec and
[docs/assumptions.md](docs/assumptions.md) for environment-specific decisions.

## Status: M1 — Contract + Agent skeleton

- `proto/uiadapter.proto`: full gRPC contract (session lifecycle, scan, replay,
  self-healing, events, screenshots).
- `agent/`: C# .NET 8 `SapGuiAgent` — dynpro-family scanning/replay, statusbar events,
  screenshots, allowlist guardrail. GuiShell/GuiTableControl are recognized but marked
  `unmapped` (full coverage is M2).
- `core/`: Python core — `UiAgentPort` seam, real gRPC client, `FakeUiAgent` (fixture
  replay), a Typer CLI driving a YAML step list through either.

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

## M1 demo

Drive a YAML step list through the agent — offline, against the recorded fixture:

```
cd core
.venv/Scripts/python -m smt.cli.main examples/va01_steps.yaml \
  --fixture tests/fixtures/va01_minimal.json
```

Or against a real, running `SapGuiAgent` with an open SAP GUI connection:

```
.venv/Scripts/python -m smt.cli.main examples/va01_steps.yaml --target localhost:50051
```

## Known gaps (tracked for later milestones)

- GuiShell (ALV grid/tree/text edit/other) and GuiTableControl replay/scan — M2.
- Self-healing (`ResolveLocator`) — M5.
- Repository, business process modeling, AI services, dashboards — M3/M6/M7.
- Nothing here has been exercised against a live, authenticated SAP GUI session yet;
  COM member names marked `VERIFY-ON-TARGET` in `agent/SapGuiAgent/Com` and
  `Components` need a targeted integration test on a real system.
