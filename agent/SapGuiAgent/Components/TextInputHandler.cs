using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiTextField, GuiCTextField, GuiPasswordField.</summary>
public sealed class TextInputHandler : ComponentHandlerBase, ITextInputHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyTextInput;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType is "GuiTextField" or "GuiCTextField" or "GuiPasswordField";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        dynamic native = component.Native;
        var masked = component.Type == "GuiPasswordField";

        switch (request.Op)
        {
            case ActionOp.Read:
            {
                string text = native.Text;
                return Task.FromResult(new ActionResult { Success = true, ActualValue = masked ? "" : text, Masked = masked });
            }
            case ActionOp.Set:
                native.Text = request.Params.TextValue;
                return Task.FromResult(new ActionResult
                {
                    Success = true,
                    ActualValue = masked ? "" : request.Params.TextValue,
                    Masked = masked,
                });
            case ActionOp.Verify:
            {
                string actual = native.Text;
                var ok = Compare(actual, request.Params);
                return Task.FromResult(new ActionResult
                {
                    Success = ok,
                    ActualValue = masked ? "" : actual,
                    Masked = masked,
                    ErrorMessage = ok ? "" : $"expected '{request.Params.ExpectedValue}' but was '{(masked ? "***" : actual)}'",
                });
            }
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on {component.Type}");
        }
    }
}
