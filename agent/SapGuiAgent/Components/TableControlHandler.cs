using System.Linq;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiTableControl (classic dynpro table, e.g. VA01's item overview — distinct from
/// the GuiShell/GridView ALV grid AlvGridHandler covers). Column-title metadata on scan (so a
/// table cell's caption can resolve to its real column header, e.g. RV45A-MABNR's column title
/// "Material"), plus absolute-row cell get/set: a captured attribute's own component_id always
/// encodes ONE specific row (e.g. "...[1,3]" — confirmed live, a scanned/picked cell is whatever
/// row happened to be visible at capture time), so driving a data-driven test across N order
/// lines needs the ROW supplied at runtime instead — TABLE_GET_CELL/TABLE_SET_CELL take the
/// table control itself as the target component_id, with the row (ActionParams.row) and column
/// index (ActionParams.column_id, stringified — GuiTableColumn has no documented technical-name
/// property to key by, only display order) supplied per call, mirroring how ALV grid ops already
/// work in AlvGridHandler.</summary>
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
        var native = new ComHandle(component.Native);
        switch (request.Op)
        {
            case ActionOp.TableGetCell:
            {
                var value = GetCellText(native, request.Params.Row, request.Params.ColumnId);
                return Task.FromResult(new ActionResult { Success = true, ActualValue = value });
            }
            case ActionOp.TableSetCell:
            {
                SetCellText(native, request.Params.Row, request.Params.ColumnId, request.Params.TextValue);
                var actual = GetCellText(native, request.Params.Row, request.Params.ColumnId);
                return Task.FromResult(new ActionResult { Success = true, ActualValue = actual });
            }
            default:
                throw new UnsupportedOperationException(
                    $"GuiTableControl does not support {request.Op} yet (planned for M2 — see spec §5 coverage matrix)");
        }
    }

    // VERIFY-ON-TARGET: GuiTableControl.GetAbsoluteRow(int) — returns the GuiTableRow for a
    // given 0-based absolute row index, scrolling the table into view internally if needed
    // (so callers never have to do their own scroll math). GuiTableRow.Item(columnIndex) then
    // returns that row's cell as a plain GuiComponent (GuiCTextField/GuiTextField/...), on
    // which .Text reads/writes the value directly like any other text-input control.
    private static ComHandle GetCell(ComHandle table, int row, string columnId)
    {
        var columnIndex = int.Parse(columnId);
        return table.CallCom("GetAbsoluteRow", row).CallCom("Item", columnIndex);
    }

    private static string GetCellText(ComHandle table, int row, string columnId) =>
        GetCell(table, row, columnId).GetString("Text");

    private static void SetCellText(ComHandle table, int row, string columnId, string value) =>
        GetCell(table, row, columnId).Set("Text", value);
}
