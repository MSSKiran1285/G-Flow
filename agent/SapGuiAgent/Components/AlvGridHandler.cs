using System.Linq;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiShell/GridView (ALV grid) — read-only slice for M2: row/column metadata on
/// scan, cell reads on replay. Table-browser output (SE16N, VA05, ME2M, ...) is almost
/// always an ALV grid, so this is what actually lets test-data mining read real historical
/// documents instead of guessing valid field combinations through blind trial and error.
/// Write ops (SET, toolbar/context-menu, checkbox/button cells) are intentionally out of
/// scope here — a fast-follow once real target screens for those exist.</summary>
public sealed class AlvGridHandler : ComponentHandlerBase, IAlvGridHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyAlvGrid;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType == "GuiShell" && sapSubType == "GridView";

    public override void EnrichSnapshot(IComComponent component, ComponentNode node, ScanDepthOptions depth)
    {
        var native = new ComHandle(component.Native);
        var detail = new GridViewDetail
        {
            RowCount = ComHandle.TryGet(() => native.GetInt("RowCount"), 0),
            VisibleRowCount = ComHandle.TryGet(() => native.GetInt("VisibleRowCount"), 0),
        };

        // VERIFY-ON-TARGET: GuiGridView.ColumnOrder — collection of technical column names
        // in display order. Display titles (GetColumnTitles) aren't extracted yet — tech
        // names alone are enough to drive mining/reads; add titles once a real need shows up.
        foreach (var columnId in ComHandle.TryGet(() => native.Collection("ColumnOrder").ToList(), new List<ComHandle>()))
        {
            var techName = ComHandle.TryGet(() => (string)columnId.Target, "");
            detail.Columns.Add(new GridColumn { ColumnId = techName, TechName = techName, Title = techName });
        }

        node.ShellDetail = new ShellDetail { GridView = detail };
    }

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        var native = new ComHandle(component.Native);
        switch (request.Op)
        {
            case ActionOp.GridGetCell:
            {
                // VERIFY-ON-TARGET: GuiGridView.GetCellValue(row, columnId)
                var value = native.Call("GetCellValue", request.Params.Row, request.Params.ColumnId) as string ?? "";
                return Task.FromResult(new ActionResult { Success = true, ActualValue = value });
            }
            case ActionOp.GridSetScrollRow:
                native.Set("FirstVisibleRow", request.Params.Row); // VERIFY-ON-TARGET
                return Task.FromResult(new ActionResult { Success = true });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiShell/GridView yet");
        }
    }
}
