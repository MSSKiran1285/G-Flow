using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class TextInputHandlerTests
{
    [Fact]
    public async Task Set_writes_text_and_returns_it_as_actual_value()
    {
        var native = new FakeTextFieldNative();
        var component = new FakeComComponent { Id = "wnd[0]/usr/ctxtVBAK-AUART", Type = "GuiCTextField", NativeObject = native };
        var handler = new TextInputHandler();

        var result = await handler.ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.Set, Params = new ActionParams { TextValue = "OR" } },
            CancellationToken.None);

        Assert.True(result.Success);
        Assert.Equal("OR", native.Text);
        Assert.Equal("OR", result.ActualValue);
    }

    [Fact]
    public async Task Read_masks_password_fields()
    {
        var native = new FakeTextFieldNative { Text = "secret" };
        var component = new FakeComComponent { Id = "wnd[0]/usr/pwdRSYST-BCODE", Type = "GuiPasswordField", NativeObject = native };
        var handler = new TextInputHandler();

        var result = await handler.ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.Read },
            CancellationToken.None);

        Assert.True(result.Success);
        Assert.True(result.Masked);
        Assert.Equal("", result.ActualValue);
    }

    [Fact]
    public async Task Verify_fails_with_readable_error_when_mismatched()
    {
        var native = new FakeTextFieldNative { Text = "OR" };
        var component = new FakeComComponent { Id = "wnd[0]/usr/ctxtVBAK-AUART", Type = "GuiCTextField", NativeObject = native };
        var handler = new TextInputHandler();

        var result = await handler.ExecuteAsync(
            component,
            new ActionRequest
            {
                ComponentId = component.Id,
                Op = ActionOp.Verify,
                Params = new ActionParams { ExpectedValue = "TA", Comparator = "equals" },
            },
            CancellationToken.None);

        Assert.False(result.Success);
        Assert.Contains("TA", result.ErrorMessage);
        Assert.Contains("OR", result.ErrorMessage);
    }

    [Fact]
    public async Task Unsupported_op_returns_failure_with_reason_instead_of_throwing()
    {
        var component = new FakeComComponent { Id = "wnd[0]/usr/ctxtVBAK-AUART", Type = "GuiCTextField", NativeObject = new FakeTextFieldNative() };
        var handler = new TextInputHandler();

        var result = await handler.ExecuteAsync(
            component,
            new ActionRequest { ComponentId = component.Id, Op = ActionOp.TreeExpand },
            CancellationToken.None);

        Assert.False(result.Success);
        Assert.NotEmpty(result.UnsupportedReason);
    }
}
