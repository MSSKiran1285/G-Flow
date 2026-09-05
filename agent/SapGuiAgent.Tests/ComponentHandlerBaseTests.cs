using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class ComponentHandlerBaseTests
{
    private static FakeComComponent BuildField(FakeTextFieldNative native)
    {
        return new FakeComComponent { Id = "wnd[0]/usr/ctxtVBAK-AUART", Type = "GuiCTextField", NativeObject = native };
    }

    [Fact]
    public async Task Highlight_is_handled_universally_by_calling_Visualize_true()
    {
        var native = new FakeTextFieldNative();
        var component = BuildField(native);

        var result = await new TextInputHandler().ExecuteAsync(
            component, new ActionRequest { ComponentId = component.Id, Op = ActionOp.Highlight }, CancellationToken.None);

        Assert.True(result.Success);
        Assert.True(native.Visualized);
    }

    [Fact]
    public async Task SetFocus_is_handled_universally_by_calling_SetFocus()
    {
        var native = new FakeTextFieldNative();
        var component = BuildField(native);

        var result = await new TextInputHandler().ExecuteAsync(
            component, new ActionRequest { ComponentId = component.Id, Op = ActionOp.SetFocus }, CancellationToken.None);

        Assert.True(result.Success);
        Assert.True(native.Focused);
    }
}
