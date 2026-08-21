using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>Fallback for families the M1 milestone doesn't implement yet — GuiShell (ALV
/// grid/tree/text edit/other shells), GuiTableControl, and anything unrecognized. Never
/// silently drops or fakes success (spec §11): scan marks the node `unmapped`, replay raises
/// UnsupportedOperation. Full coverage lands in M2 per the delivery plan.</summary>
public sealed class NotYetImplementedHandler : ComponentHandlerBase,
    ITableControlHandler, IAlvGridHandler, ITreeHandler, ITextShellHandler, IOtherShellHandler
{
    private readonly ComponentFamily _family;

    public NotYetImplementedHandler(ComponentFamily family)
    {
        _family = family;
    }

    public override ComponentFamily Family => _family;

    public override bool CanHandle(string sapType, string sapSubType) => true; // catch-all; registry picks last

    public override void EnrichSnapshot(IComComponent component, ComponentNode node, ScanDepthOptions depth)
    {
        node.Unmapped = true;
        node.CoverageStatus = "unsupported";
    }

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        throw new UnsupportedOperationException(
            $"{component.Type}" + (string.IsNullOrEmpty(component.SubType) ? "" : $"/{component.SubType}") +
            " is not implemented yet (planned for M2 — see spec §5 coverage matrix)");
    }
}
