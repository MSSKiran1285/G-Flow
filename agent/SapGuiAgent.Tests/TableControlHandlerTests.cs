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
    public async Task ExecuteAsync_still_unsupported_ops_fail_honestly()
    {
        var component = BuildTable(new FakeTableControlNative());

        var result = await new TableControlHandler().ExecuteAsync(
            component, new ActionRequest { ComponentId = component.Id, Op = ActionOp.Read }, CancellationToken.None);

        Assert.False(result.Success);
        Assert.Contains("GuiTableControl", result.UnsupportedReason);
    }

    [Fact]
    public async Task TableGetCell_reads_the_requested_absolute_row_and_column()
    {
        var native = new FakeTableControlNative();
        native.GetAbsoluteRow(3).Item(1).Text = "TG-0007";
        var component = BuildTable(native);

        var result = await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TableGetCell, Params = new ActionParams { Row = 3, ColumnId = "1" } },
            CancellationToken.None);

        Assert.True(result.Success);
        Assert.Equal("TG-0007", result.ActualValue);
    }

    [Fact]
    public async Task TableSetCell_writes_the_value_and_returns_it_back()
    {
        var native = new FakeTableControlNative();
        var component = BuildTable(native);

        var result = await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest
            {
                ComponentId = component.Id, Op = ActionOp.TableSetCell,
                Params = new ActionParams { Row = 5, ColumnId = "2", TextValue = "10" },
            },
            CancellationToken.None);

        Assert.True(result.Success);
        Assert.Equal("10", result.ActualValue);
        Assert.Equal("10", native.GetAbsoluteRow(5).Item(2).Text);
    }

    [Fact]
    public async Task TableGetCell_and_TableSetCell_address_different_rows_independently()
    {
        // The whole point of runtime row addressing: the same column/component_id (the
        // table control itself), different `row` params, must not collide — this is what
        // makes a data-driven multi-line-item test case possible.
        var native = new FakeTableControlNative();
        var component = BuildTable(native);

        await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TableSetCell, Params = new ActionParams { Row = 0, ColumnId = "1", TextValue = "MAT-A" } },
            CancellationToken.None);
        await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TableSetCell, Params = new ActionParams { Row = 1, ColumnId = "1", TextValue = "MAT-B" } },
            CancellationToken.None);

        var row0 = await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TableGetCell, Params = new ActionParams { Row = 0, ColumnId = "1" } },
            CancellationToken.None);
        var row1 = await new TableControlHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TableGetCell, Params = new ActionParams { Row = 1, ColumnId = "1" } },
            CancellationToken.None);

        Assert.Equal("MAT-A", row0.ActualValue);
        Assert.Equal("MAT-B", row1.ActualValue);
    }
}
