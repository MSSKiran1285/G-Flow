using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiButton, GuiOkCodeField, GuiMenubar/GuiMenu (path-based), GuiToolbar.</summary>
public sealed class ActionHandler : ComponentHandlerBase, IActionHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyAction;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType is "GuiButton" or "GuiOkCodeField" or "GuiMenubar" or "GuiMenu" or "GuiToolbar";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        return component.Type switch
        {
            "GuiButton" => HandleButton(component, request),
            "GuiOkCodeField" => HandleOkCodeField(component, request),
            "GuiMenubar" or "GuiMenu" => HandleMenu(component, request),
            _ => throw new UnsupportedOperationException($"{request.Op} is not supported on {component.Type} yet"),
        };
    }

    private static Task<ActionResult> HandleButton(IComComponent component, ActionRequest request)
    {
        if (request.Op != ActionOp.Press)
        {
            throw new UnsupportedOperationException($"{request.Op} is not supported on GuiButton");
        }
        new ComHandle(component.Native).Call("Press"); // VERIFY-ON-TARGET: GuiButton.Press()
        return Task.FromResult(new ActionResult { Success = true });
    }

    private static Task<ActionResult> HandleOkCodeField(IComComponent component, ActionRequest request)
    {
        var native = new ComHandle(component.Native);
        switch (request.Op)
        {
            case ActionOp.Read:
                return Task.FromResult(new ActionResult { Success = true, ActualValue = native.GetString("Text") });
            case ActionOp.Set:
                native.Set("Text", request.Params.TextValue); // e.g. "/nVA02", "/o"
                return Task.FromResult(new ActionResult { Success = true, ActualValue = request.Params.TextValue });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiOkCodeField");
        }
    }

    private static Task<ActionResult> HandleMenu(IComComponent component, ActionRequest request)
    {
        if (request.Op != ActionOp.MenuSelect)
        {
            throw new UnsupportedOperationException($"{request.Op} is not supported on {component.Type}");
        }

        var target = new ComHandle(component.Native);
        if (!string.IsNullOrEmpty(request.Params.MenuPath))
        {
            foreach (var segment in request.Params.MenuPath.Split("->", StringSplitOptions.TrimEntries))
            {
                target = FindChildByText(target, segment)
                    ?? throw new UnsupportedOperationException(
                        $"menu path segment '{segment}' not found under '{request.Params.MenuPath}'");
            }
        }

        target.Call("Select"); // VERIFY-ON-TARGET: GuiMenu.Select()
        return Task.FromResult(new ActionResult { Success = true });
    }

    private static ComHandle? FindChildByText(ComHandle menuOrMenubar, string text)
    {
        // VERIFY-ON-TARGET: GuiMenubar/GuiMenu.Children
        foreach (var child in menuOrMenubar.Collection("Children"))
        {
            if (string.Equals(child.GetString("Text"), text, StringComparison.OrdinalIgnoreCase))
            {
                return child;
            }
        }
        return null;
    }
}
