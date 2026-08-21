using System.Collections.Generic;

namespace SapGuiAgent.Com;

/// <summary>
/// Wraps one SAP GUI Scripting COM component (GuiComponent) behind a testable seam.
/// All COM interop lives behind this interface so SapGuiAgent.Tests can substitute a fake
/// (§11) without touching real COM.
///
/// Trade-off (documented per spec §1/§13): this environment has no Windows SDK / Visual
/// Studio tlbimp and no registry access, so the early-bound SAPFEWSELib interop assembly
/// described in spec §2 cannot be generated here. Components are accessed late-bound via
/// `dynamic` (IDispatch) instead — `Native` exposes the raw COM object. Everything above
/// this interface (handlers, scanner, gRPC service) stays statically typed; only the
/// innermost member access on `Native` is dynamic. See docs/assumptions.md.
/// </summary>
public interface IComComponent
{
    string Id { get; }
    string Type { get; }          // raw GuiComponent.Type
    int TypeAsNumber { get; }     // raw GuiComponent.TypeAsNumber
    string SubType { get; }       // raw shell SubType; "" when not a GuiShell
    string Name { get; }
    IReadOnlyList<IComComponent> Children { get; }

    /// <summary>The underlying COM object (late-bound). Handlers call family-specific
    /// members on this directly, e.g. `component.Native.Text = value`.</summary>
    dynamic Native { get; }
}
