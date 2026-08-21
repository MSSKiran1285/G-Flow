using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class ComponentHandlerRegistryTests
{
    [Fact]
    public void Resolve_returns_registered_handler_for_known_type()
    {
        var registry = ComponentHandlerRegistry.CreateDefault();
        var handler = registry.Resolve("GuiTextField", "");
        Assert.IsType<TextInputHandler>(handler);
        Assert.Equal(ComponentFamily.FamilyTextInput, handler.Family);
    }

    [Fact]
    public void Resolve_falls_back_to_NotYetImplemented_for_unimplemented_shell_family()
    {
        var registry = ComponentHandlerRegistry.CreateDefault();
        var handler = registry.Resolve("GuiShell", "GridView");
        Assert.IsType<NotYetImplementedHandler>(handler);
        Assert.Equal(ComponentFamily.FamilyAlvGrid, handler.Family);
    }

    [Fact]
    public void NotYetImplemented_marks_node_unmapped_instead_of_dropping_it()
    {
        var registry = ComponentHandlerRegistry.CreateDefault();
        var handler = registry.Resolve("GuiTableControl", "");
        var component = new FakeComComponent { Id = "wnd[0]/usr/tblX", Type = "GuiTableControl" };
        var node = new ComponentNode { Id = component.Id, Type = component.Type };

        handler.EnrichSnapshot(component, node, new ScanDepthOptions());

        Assert.True(node.Unmapped);
        Assert.Equal("unsupported", node.CoverageStatus);
    }

    [Fact]
    public async Task NotYetImplemented_raises_UnsupportedOperation_on_execute_rather_than_faking_success()
    {
        var registry = ComponentHandlerRegistry.CreateDefault();
        var handler = registry.Resolve("GuiTableControl", "");
        var component = new FakeComComponent { Id = "wnd[0]/usr/tblX", Type = "GuiTableControl" };

        var result = await handler.ExecuteAsync(component, new ActionRequest { ComponentId = component.Id, Op = ActionOp.Read }, CancellationToken.None);

        Assert.False(result.Success);
        Assert.Contains("GuiTableControl", result.UnsupportedReason);
    }
}
