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
