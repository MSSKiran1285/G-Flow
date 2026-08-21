using System.Linq;
using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class AlvGridHandlerTests
{
    private static FakeComComponent BuildGrid(FakeGridViewNative native)
    {
        return new FakeComComponent
        {
            Id = "wnd[0]/usr/shellcont/shell",
            Type = "GuiShell",
            SubType = "GridView",
            NativeObject = native,
        };
    }

    [Fact]
    public void EnrichSnapshot_populates_row_count_and_columns()
    {
        var native = new FakeGridViewNative { RowCount = 42, VisibleRowCount = 10 };
        native.ColumnOrder.Add("VBELN");
        native.ColumnOrder.Add("KUNNR");
        var component = BuildGrid(native);
        var node = new ComponentNode { Id = component.Id, Type = component.Type, SubType = component.SubType };

        new AlvGridHandler().EnrichSnapshot(component, node, new ScanDepthOptions());

        Assert.Equal(42, node.ShellDetail.GridView.RowCount);
        Assert.Equal(10, node.ShellDetail.GridView.VisibleRowCount);
        Assert.Equal(new[] { "VBELN", "KUNNR" }, node.ShellDetail.GridView.Columns.Select(c => c.TechName));
        Assert.False(node.Unmapped);
    }

    [Fact]
    public async Task GridGetCell_reads_the_requested_cell()
    {
        var native = new FakeGridViewNative();
        native.Cells[(0, "VBELN")] = "0000000123";
        var component = BuildGrid(native);

        var result = await new AlvGridHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.GridGetCell, Params = new ActionParams { Row = 0, ColumnId = "VBELN" } },
            CancellationToken.None);

        Assert.True(result.Success);
        Assert.Equal("0000000123", result.ActualValue);
    }

    [Fact]
    public async Task Unsupported_op_fails_honestly_instead_of_faking_success()
    {
        var component = BuildGrid(new FakeGridViewNative());

        var result = await new AlvGridHandler().ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.GridSelectRows },
            CancellationToken.None);

        Assert.False(result.Success);
        Assert.NotEmpty(result.UnsupportedReason);
    }
}
