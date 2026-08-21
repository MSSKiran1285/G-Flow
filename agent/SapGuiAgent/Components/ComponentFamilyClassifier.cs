using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>Maps a SAP-reported (Type, SubType) pair to our own §5 routing taxonomy. This
/// enum is ours, not SAP's — see the note on ComponentFamily in uiadapter.proto.</summary>
public static class ComponentFamilyClassifier
{
    public static ComponentFamily Classify(string sapType, string sapSubType)
    {
        return sapType switch
        {
            "GuiTextField" or "GuiCTextField" or "GuiPasswordField" => ComponentFamily.FamilyTextInput,
            "GuiComboBox" or "GuiCheckBox" or "GuiRadioButton" => ComponentFamily.FamilySelection,
            "GuiButton" or "GuiOkCodeField" or "GuiMenubar" or "GuiMenu" or "GuiToolbar" => ComponentFamily.FamilyAction,
            "GuiTabStrip" or "GuiTab" or "GuiSimpleContainer" or "GuiScrollContainer"
                or "GuiUserArea" or "GuiBox" or "GuiLabel" or "GuiContainerShell"
                or "GuiTitlebar" or "GuiCustomControl" => ComponentFamily.FamilyStructure,
            "GuiMainWindow" or "GuiModalWindow" or "GuiFrameWindow" => ComponentFamily.FamilyWindow,
            "GuiStatusbar" or "GuiStatusPane" => ComponentFamily.FamilyStatusbar,
            "GuiTableControl" => ComponentFamily.FamilyTableControl,
            "GuiShell" => ClassifyShell(sapSubType),
            // Some shell-family controls report a specific .Type directly (e.g.
            // "GuiSplitterShell") instead of "GuiShell" + SubType — seen live (§ M1
            // findings); route those through the same shell classifier.
            _ when sapType.EndsWith("Shell", StringComparison.Ordinal) => ClassifyShell(sapSubType),
            _ => ComponentFamily.FamilyUnknown,
        };
    }

    private static ComponentFamily ClassifyShell(string subType) => subType switch
    {
        "GridView" => ComponentFamily.FamilyAlvGrid,
        "Tree" => ComponentFamily.FamilyTree,
        "TextEdit" => ComponentFamily.FamilyTextShell,
        _ => ComponentFamily.FamilyOtherShell,
    };
}
