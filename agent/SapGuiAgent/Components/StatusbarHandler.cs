using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiStatusbar. The message-pattern registry that auto-extracts created document
/// numbers into buffers (spec §5) is core-side (it runs against StatusbarMessage in
/// ActionResult/UiEvent) — this handler only reads the raw message.</summary>
public sealed class StatusbarHandler : ComponentHandlerBase, IStatusbarHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyStatusbar;

    public override bool CanHandle(string sapType, string sapSubType) => sapType == "GuiStatusbar";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        dynamic native = component.Native;
        switch (request.Op)
        {
            case ActionOp.StatusbarRead:
            {
                var message = ReadMessage(native);
                var result = new ActionResult { Success = true, ActualValue = message.Text };
                result.StatusbarDeltas.Add(message);
                return Task.FromResult(result);
            }
            case ActionOp.StatusbarOpenLongText:
                native.DoubleClick(); // VERIFY-ON-TARGET: GuiStatusbar.DoubleClick()
                return Task.FromResult(new ActionResult { Success = true });
            default:
                throw new UnsupportedOperationException($"{request.Op} is not supported on GuiStatusbar");
        }
    }

    // VERIFY-ON-TARGET: GuiStatusbar member names (MessageType/MessageId/MessageNumber/Text).
    internal static StatusbarMessage ReadMessage(dynamic native) => new()
    {
        Type = SapGuiComComponent.TryGet(() => (string)native.MessageType, ""),
        Text = SapGuiComComponent.TryGet(() => (string)native.Text, ""),
        MessageId = SapGuiComComponent.TryGet(() => (string)native.MessageId, ""),
        MessageNumber = SapGuiComComponent.TryGet(() => (string)native.MessageNumber, ""),
    };
}
