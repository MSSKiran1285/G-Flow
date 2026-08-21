using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiComboBox, GuiCheckBox, GuiRadioButton — select by key and by visible text.</summary>
public sealed class SelectionHandler : ComponentHandlerBase, ISelectionHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilySelection;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType is "GuiComboBox" or "GuiCheckBox" or "GuiRadioButton";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        return component.Type switch
        {
            "GuiComboBox" => HandleComboBox(component, request),
            "GuiCheckBox" => HandleCheckBox(component, request),
            "GuiRadioButton" => HandleRadioButton(component, request),
            _ => throw new UnsupportedOperationException($"unhandled selection type {component.Type}"),
        };
    }

    private static Task<ActionResult> HandleComboBox(IComComponent component, ActionRequest request)
    {
        dynamic native = component.Native;
        switch (request.Op)
        {
            case ActionOp.Read:
                return Task.FromResult(new ActionResult { Success = true, ActualValue = (string)native.Key });
            case ActionOp.Select:
                if (!string.IsNullOrEmpty(request.Params.KeyValue))
                {
                    native.Key = request.Params.KeyValue; // VERIFY-ON-TARGET: GuiComboBox.Key
                }
                else if (!string.IsNullOrEmpty(request.Params.VisibleTextValue))
                {
                    // VERIFY-ON-TARGET: GuiComboBox.Entries is a GuiComponentCollection of
                    // GuiComboBoxEntry (Key, Value); find the entry whose Value matches.
                    dynamic entries = native.Entries;
                    int count = (int)entries.Count;
                    var matched = false;
                    for (var i = 0; i < count; i++)
                    {
                        dynamic entry = entries.ElementAt(i);
                        if ((string)entry.Value == request.Params.VisibleTextValue)
                        {
                            native.Key = (string)entry.Key;
                            matched = true;
                            break;
                        }
                    }
                    if (!matched)
                    {
                        throw new UnsupportedOperationException(
                            $"no combo box entry with visible text '{request.Params.VisibleTextValue}'");
                    }
                }
                else
                {
                    throw new UnsupportedOperationException("SELECT requires key_value or visible_text_value");
                }
                return Task.FromResult(new ActionResult { Success = true, ActualValue = (string)native.Key });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiComboBox");
        }
    }

    private static Task<ActionResult> HandleCheckBox(IComComponent component, ActionRequest request)
    {
        dynamic native = component.Native; // VERIFY-ON-TARGET: GuiCheckBox.Selected (bool)
        switch (request.Op)
        {
            case ActionOp.Read:
                return Task.FromResult(new ActionResult { Success = true, ActualValue = ((bool)native.Selected).ToString() });
            case ActionOp.Select:
                var value = string.IsNullOrEmpty(request.Params.KeyValue) || request.Params.KeyValue != "false";
                native.Selected = value;
                return Task.FromResult(new ActionResult { Success = true, ActualValue = value.ToString() });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiCheckBox");
        }
    }

    private static Task<ActionResult> HandleRadioButton(IComComponent component, ActionRequest request)
    {
        dynamic native = component.Native; // VERIFY-ON-TARGET: GuiRadioButton.Selected (bool)
        switch (request.Op)
        {
            case ActionOp.Read:
                return Task.FromResult(new ActionResult { Success = true, ActualValue = ((bool)native.Selected).ToString() });
            case ActionOp.Select:
                native.Selected = true;
                return Task.FromResult(new ActionResult { Success = true, ActualValue = "true" });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiRadioButton");
        }
    }
}
