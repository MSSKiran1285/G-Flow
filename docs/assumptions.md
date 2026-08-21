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
