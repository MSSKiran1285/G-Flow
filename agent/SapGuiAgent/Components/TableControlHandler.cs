using System.Linq;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiTableControl (classic dynpro table, e.g. VA01's item overview — distinct from
/// the GuiShell/GridView ALV grid AlvGridHandler covers) — read-only column-title metadata on
/// scan for M1, so a table cell's caption can resolve to its real column header (e.g.
/// RV45A-MABNR's column title "Material") instead of nothing. Row/cell get-set ops are M2
/// scope (spec §5 coverage matrix) — still unimplemented here, same as before this handler
/// existed.</summary>
public sealed class TableControlHandler : ComponentHandlerBase, ITableControlHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyTableControl;

    public override bool CanHandle(string sapType, string sapSubType) => sapType == "GuiTableControl";

    public override void EnrichSnapshot(IComComponent component, ComponentNode node, ScanDepthOptions depth)
    {
        var native = new ComHandle(component.Native);
        var detail = new TableControlDetail
        {
            RowCount = ComHandle.TryGet(() => native.GetInt("RowCount"), 0),
            VisibleRowCount = ComHandle.TryGet(() => native.GetInt("VisibleRowCount"), 0),
        };

        // VERIFY-ON-TARGET: GuiTableControl.Columns — a GuiCollection of GuiTableColumn, each
        // exposing .Title (the displayed header text). Columns are in the same left-to-right
        // display order as a cell's own "[col,row]" id suffix, so column index doubles as the
        // lookup key for FindCaptionByColumn without needing a separate technical-name match.
        // .ToList() forces enumeration inside the TryGet delegate — Collection() is a lazy
        // iterator, so without it a COM failure would throw on the `foreach` below instead of
        // being caught here (same pattern AlvGridHandler.EnrichSnapshot uses for ColumnOrder).
        foreach (var column in ComHandle.TryGet(() => native.Collection("Columns").ToList(), new List<ComHandle>()))
        {
            var title = ComHandle.TryGet(() => column.GetString("Title"), "");
            detail.Columns.Add(new TableColumn { Title = title });
        }

        node.TableDetail = detail;
    }

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        throw new UnsupportedOperationException(
            "GuiTableControl row/cell ops not implemented yet (planned for M2 — see spec §5 coverage matrix)");
    }
}
