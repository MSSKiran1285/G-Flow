using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiMainWindow, GuiModalWindow, GuiFrameWindow. Also carries SEND_VKEY (spec §5
/// "Legacy/batch" row: SendVKey lives on the window, not the focused control), so this
/// class doubles as the ILegacyHandler for that op.</summary>
public sealed class WindowHandler : ComponentHandlerBase, IWindowHandler, ILegacyHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyWindow;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType is "GuiMainWindow" or "GuiModalWindow" or "GuiFrameWindow";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        dynamic native = component.Native;
        switch (request.Op)
        {
            case ActionOp.SendVkey:
                native.SendVKey(VKeyCodes.Resolve(request.Params.Vkey)); // VERIFY-ON-TARGET
                return Task.FromResult(new ActionResult { Success = true });
            case ActionOp.WindowMaximize:
                native.Maximize(); // VERIFY-ON-TARGET: GuiFrameWindow.Maximize()
                return Task.FromResult(new ActionResult { Success = true });
            case ActionOp.WindowResize:
                native.ResizeWorkingPane(request.Params.Row, request.Params.SashPosition, false); // VERIFY-ON-TARGET signature
                return Task.FromResult(new ActionResult { Success = true });
            case ActionOp.WindowClose:
                native.Close(); // VERIFY-ON-TARGET: GuiFrameWindow.Close()
                return Task.FromResult(new ActionResult { Success = true });
            case ActionOp.Verify:
                string title = native.Text;
                var ok = Compare(title, request.Params);
                return Task.FromResult(new ActionResult
                {
                    Success = ok,
                    ActualValue = title,
                    ErrorMessage = ok ? "" : $"expected title '{request.Params.ExpectedValue}' but was '{title}'",
                });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on {component.Type}");
        }
    }
}

/// <summary>Symbolic VKey names (spec §5: "Enter", "F3", "F8", "Ctrl+S", ...) to the integer
/// codes SAP GUI Scripting expects. VERIFY-ON-TARGET against the real VKey table — these are
/// the commonly documented values but must be confirmed on a live system.</summary>
public static class VKeyCodes
{
    private static readonly Dictionary<string, int> Map = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Enter"] = 0,
        ["F1"] = 1,
        ["F2"] = 2,
        ["F3"] = 3,
        ["F4"] = 4,
        ["F5"] = 5,
        ["F6"] = 6,
        ["F7"] = 7,
        ["F8"] = 8,
        ["F9"] = 9,
        ["F10"] = 10,
        ["F11"] = 11,
        ["F12"] = 12,
        ["Ctrl+S"] = 11,
        ["ShiftF4"] = 16,
    };

    public static int Resolve(string symbolic)
    {
        if (int.TryParse(symbolic, out var raw)) return raw;
        if (Map.TryGetValue(symbolic, out var code)) return code;
        throw new UnsupportedOperationException($"unknown VKey symbol '{symbolic}'");
    }
}
