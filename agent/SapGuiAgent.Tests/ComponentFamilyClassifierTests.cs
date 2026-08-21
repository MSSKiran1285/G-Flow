using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using Xunit;

namespace SapGuiAgent.Tests;

public class ComponentFamilyClassifierTests
{
    [Theory]
    [InlineData("GuiTextField", "", ComponentFamily.FamilyTextInput)]
    [InlineData("GuiCTextField", "", ComponentFamily.FamilyTextInput)]
    [InlineData("GuiPasswordField", "", ComponentFamily.FamilyTextInput)]
    [InlineData("GuiComboBox", "", ComponentFamily.FamilySelection)]
    [InlineData("GuiCheckBox", "", ComponentFamily.FamilySelection)]
    [InlineData("GuiButton", "", ComponentFamily.FamilyAction)]
    [InlineData("GuiOkCodeField", "", ComponentFamily.FamilyAction)]
    [InlineData("GuiMenubar", "", ComponentFamily.FamilyAction)]
    [InlineData("GuiTabStrip", "", ComponentFamily.FamilyStructure)]
    [InlineData("GuiLabel", "", ComponentFamily.FamilyStructure)]
    [InlineData("GuiMainWindow", "", ComponentFamily.FamilyWindow)]
    [InlineData("GuiStatusbar", "", ComponentFamily.FamilyStatusbar)]
    [InlineData("GuiTableControl", "", ComponentFamily.FamilyTableControl)]
    [InlineData("GuiShell", "GridView", ComponentFamily.FamilyAlvGrid)]
    [InlineData("GuiShell", "Tree", ComponentFamily.FamilyTree)]
    [InlineData("GuiShell", "TextEdit", ComponentFamily.FamilyTextShell)]
    [InlineData("GuiShell", "Calendar", ComponentFamily.FamilyOtherShell)]
    [InlineData("GuiSomeFutureType", "", ComponentFamily.FamilyUnknown)]
    public void Classify_maps_sap_type_and_subtype_to_family(string sapType, string subType, ComponentFamily expected)
    {
        Assert.Equal(expected, ComponentFamilyClassifier.Classify(sapType, subType));
    }
}
