using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>GuiTabStrip/GuiTab, GuiSimpleContainer, GuiScrollContainer, GuiUserArea, GuiBox,
/// GuiLabel. Containers mostly just pass through the tree walk; GuiTab/GuiLabel carry the
/// only replay ops implemented here for M1.</summary>
public sealed class StructureHandler : ComponentHandlerBase, IStructureHandler
{
    public override ComponentFamily Family => ComponentFamily.FamilyStructure;

    public override bool CanHandle(string sapType, string sapSubType) =>
        sapType is "GuiTabStrip" or "GuiTab" or "GuiSimpleContainer" or "GuiScrollContainer"
            or "GuiUserArea" or "GuiBox" or "GuiLabel" or "GuiContainerShell";

    protected override Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        var native = new ComHandle(component.Native);

        if (component.Type == "GuiTab" && request.Op == ActionOp.TabSelect)
        {
            native.Call("Select"); // VERIFY-ON-TARGET: GuiTab.Select()
            return Task.FromResult(new ActionResult { Success = true });
        }

        if (component.Type == "GuiLabel")
        {
            switch (request.Op)
            {
                case ActionOp.Read:
                    return Task.FromResult(new ActionResult { Success = true, ActualValue = native.GetString("Text") });
                case ActionOp.Verify:
                    var actual = native.GetString("Text");
                    var ok = Compare(actual, request.Params);
                    return Task.FromResult(new ActionResult
                    {
                        Success = ok,
                        ActualValue = actual,
                        ErrorMessage = ok ? "" : $"expected '{request.Params.ExpectedValue}' but was '{actual}'",
                    });
            }
        }

        throw new UnsupportedOperationException($"{request.Op} is not supported on {component.Type} yet");
    }
}
