using System.Linq;
using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class TableControlHandlerTests
{
    private static FakeComComponent BuildTable(FakeTableControlNative native)
    {
        return new FakeComComponent
        {
            Id = "wnd[0]/usr/tblSAPMV45ATCTRL_UEBERSICHT",
            Type = "GuiTableControl",
            NativeObject = native,
        };
    }

    [Fact]
    public void EnrichSnapshot_populates_row_count_and_column_titles()
    {
        var native = new FakeTableControlNative { RowCount = 32, VisibleRowCount = 17 };
        native.Columns.Add(new FakeTableColumn { Title = "Item" });
        native.Columns.Add(new FakeTableColumn { Title = "Material" });
        native.Columns.Add(new FakeTableColumn { Title = "Order Quantity" });
        var component = BuildTable(native);
        var node = new ComponentNode { Id = component.Id, Type = component.Type };

        new TableControlHandler().EnrichSnapshot(component, node, new ScanDepthOptions());

        Assert.Equal(32, node.TableDetail.RowCount);
        Assert.Equal(17, node.TableDetail.VisibleRowCount);
        Assert.Equal(new[] { "Item", "Material", "Order Quantity" }, node.TableDetail.Columns.Select(c => c.Title));
        Assert.False(node.Unmapped);
    }

    [Fact]
    public void EnrichSnapshot_degrades_to_empty_columns_instead_of_crashing_when_the_native_object_has_none()
    {
        // A plain object() has no Columns/RowCount property at all — mirrors what a fake or
        // unusual COM object could report; must not throw (matches AlvGridHandler's own
        // ColumnOrder-missing behavior).
        var component = new FakeComComponent { Id = "wnd[0]/usr/tblX", Type = "GuiTableControl", NativeObject = new object() };
        var node = new ComponentNode { Id = component.Id, Type = component.Type };

        new TableControlHandler().EnrichSnapshot(component, node, new ScanDepthOptions());

        Assert.Equal(0, node.TableDetail.RowCount);
        Assert.Empty(node.TableDetail.Columns);
        Assert.False(node.Unmapped);
    }

    [Fact]
    public async Task ExecuteAsync_row_cell_ops_fail_honestly_not_yet_implemented()
    {
        var component = BuildTable(new FakeTableControlNative());

        var result = await new TableControlHandler().ExecuteAsync(
            component, new ActionRequest { ComponentId = component.Id, Op = ActionOp.Read }, CancellationToken.None);

        Assert.False(result.Success);
        Assert.Contains("GuiTableControl", result.UnsupportedReason);
    }
}
