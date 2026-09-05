using SapGuiAgent.Grpc;
using SapGuiAgent.Scanning;
using Xunit;

namespace SapGuiAgent.Tests;

public class ComponentHitTesterTests
{
    private static ComponentNode Rect(string id, int left, int top, int width, int height, params ComponentNode[] children)
    {
        var node = new ComponentNode { Id = id, ScreenLeft = left, ScreenTop = top, Width = width, Height = height };
        node.Children.AddRange(children);
        return node;
    }

    [Fact]
    public void Find_prefers_the_smallest_area_match_over_its_containing_parent()
    {
        var field = Rect("wnd[0]/usr/ctxtVBAK-AUART", 100, 100, 50, 20);
        var container = Rect("wnd[0]/usr", 0, 0, 800, 600, field);
        var root = Rect("wnd[0]", 0, 0, 800, 600, container);

        var hit = ComponentHitTester.Find(root, x: 110, y: 105);

        Assert.NotNull(hit);
        Assert.Equal("wnd[0]/usr/ctxtVBAK-AUART", hit!.Id);
    }

    [Fact]
    public void Find_returns_null_when_the_point_is_outside_every_rect()
    {
        var root = Rect("wnd[0]", 0, 0, 800, 600, Rect("wnd[0]/usr/ctxtVBAK-AUART", 100, 100, 50, 20));

        var hit = ComponentHitTester.Find(root, x: 900, y: 900);

        Assert.Null(hit);
    }

    [Fact]
    public void Find_ignores_zero_size_nodes_like_menu_entries()
    {
        var menu = Rect("wnd[0]/mbar/menu[0]", 100, 100, 0, 0);
        var root = Rect("wnd[0]", 0, 0, 800, 600, menu);

        var hit = ComponentHitTester.Find(root, x: 100, y: 100);

        Assert.NotNull(hit);
        Assert.Equal("wnd[0]", hit!.Id); // falls back to the containing root, not the zero-size menu node
    }

    [Fact]
    public void Find_picks_among_siblings_by_smallest_area_not_tree_order()
    {
        var wide = Rect("wnd[0]/usr/wide", 0, 0, 700, 500);
        var narrow = Rect("wnd[0]/usr/narrow", 100, 100, 10, 10);
        var root = Rect("wnd[0]", 0, 0, 800, 600, wide, narrow);

        var hit = ComponentHitTester.Find(root, x: 105, y: 105);

        Assert.NotNull(hit);
        Assert.Equal("wnd[0]/usr/narrow", hit!.Id);
    }

    private static ComponentNode Labelled(string id, string type, string text = "")
    {
        var node = new ComponentNode { Id = id, Type = type, Text = text };
        return node;
    }

    private static ComponentNode PositionedField(string id, string type, string text, int left, int top, int width, int height, bool changeable = true)
    {
        return new ComponentNode { Id = id, Type = type, Text = text, ScreenLeft = left, ScreenTop = top, Width = width, Height = height, Changeable = changeable };
    }

    [Fact]
    public void FindCaption_finds_the_sibling_label_by_id_convention()
    {
        var label = Labelled("wnd[0]/usr/lblVBAK-AUART", "GuiLabel", "Order Type");
        var field = Labelled("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField");
        var root = Rect("wnd[0]", 0, 0, 800, 600, label, field);

        Assert.Equal("Order Type", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_returns_empty_when_the_target_is_already_a_label()
    {
        var label = Labelled("wnd[0]/usr/lblVBAK-AUART", "GuiLabel", "Order Type");
        var root = Rect("wnd[0]", 0, 0, 800, 600, label);

        Assert.Equal("", ComponentHitTester.FindCaption(root, label));
    }

    [Fact]
    public void FindCaption_returns_empty_when_no_matching_sibling_label_exists()
    {
        var field = Labelled("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField");
        var root = Rect("wnd[0]", 0, 0, 800, 600, field);

        Assert.Equal("", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_skips_table_control_cells()
    {
        var label = Labelled("wnd[0]/usr/lblVBAK-AUART", "GuiLabel", "Order Type");
        var cell = Labelled("wnd[0]/usr/tbl/ctxtVBAK-AUART[0,0]", "GuiCTextField");
        var root = Rect("wnd[0]", 0, 0, 800, 600, label, cell);

        Assert.Equal("", ComponentHitTester.FindCaption(root, cell));
    }

    [Fact]
    public void FindCaption_works_for_program_variable_style_ids_too()
    {
        var label = Labelled("wnd[0]/usr/lblRV45A-TXT_AUART", "GuiLabel", "Order Type");
        var field = Labelled("wnd[0]/usr/txtRV45A-TXT_AUART", "GuiTextField");
        var root = Rect("wnd[0]", 0, 0, 800, 600, label, field);

        Assert.Equal("Order Type", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_falls_back_to_the_nearest_same_row_control_to_the_left_when_no_id_sibling_exists()
    {
        // Mirrors the real VA01 screen: VBAK-AUART's caption is rendered by an
        // unrelated read-only GuiTextField (RV45A-TXT_AUART), not a lbl-prefixed sibling.
        var caption = PositionedField("wnd[0]/usr/txtRV45A-TXT_AUART", "GuiTextField", "Order Type", left: 10, top: 100, width: 80, height: 20, changeable: false);
        var field = PositionedField("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField", "OR", left: 100, top: 100, width: 50, height: 20);
        var root = Rect("wnd[0]", 0, 0, 800, 600, caption, field);

        Assert.Equal("Order Type", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_positional_fallback_ignores_editable_fields_to_the_left()
    {
        // A changeable field to the left is a sibling input, not a caption — must not match.
        var otherField = PositionedField("wnd[0]/usr/ctxtVBAK-VKORG", "GuiCTextField", "GP01", left: 10, top: 100, width: 50, height: 20, changeable: true);
        var field = PositionedField("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField", "OR", left: 100, top: 100, width: 50, height: 20);
        var root = Rect("wnd[0]", 0, 0, 800, 600, otherField, field);

        Assert.Equal("", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_positional_fallback_ignores_controls_on_a_different_row()
    {
        var captionAboveNotLeft = PositionedField("wnd[0]/usr/txtOther", "GuiTextField", "Unrelated", left: 100, top: 40, width: 80, height: 20, changeable: false);
        var field = PositionedField("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField", "OR", left: 100, top: 100, width: 50, height: 20);
        var root = Rect("wnd[0]", 0, 0, 800, 600, captionAboveNotLeft, field);

        Assert.Equal("", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_positional_fallback_prefers_the_closest_candidate_when_several_qualify()
    {
        var farLabel = PositionedField("wnd[0]/usr/lblFar", "GuiLabel", "Far", left: 10, top: 100, width: 40, height: 20);
        var nearLabel = PositionedField("wnd[0]/usr/lblNear", "GuiLabel", "Near", left: 60, top: 100, width: 30, height: 20);
        var field = PositionedField("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField", "OR", left: 100, top: 100, width: 50, height: 20);
        var root = Rect("wnd[0]", 0, 0, 800, 600, farLabel, nearLabel, field);

        Assert.Equal("Near", ComponentHitTester.FindCaption(root, field));
    }

    [Fact]
    public void FindCaption_prefers_the_id_based_sibling_over_the_positional_fallback_when_both_exist()
    {
        var idLabel = Labelled("wnd[0]/usr/lblVBAK-AUART", "GuiLabel", "Order Type");
        var positionalCandidate = PositionedField("wnd[0]/usr/txtRV45A-TXT_AUART", "GuiTextField", "Wrong Caption", left: 10, top: 100, width: 80, height: 20, changeable: false);
        var field = PositionedField("wnd[0]/usr/ctxtVBAK-AUART", "GuiCTextField", "OR", left: 100, top: 100, width: 50, height: 20);
        var root = Rect("wnd[0]", 0, 0, 800, 600, idLabel, positionalCandidate, field);

        Assert.Equal("Order Type", ComponentHitTester.FindCaption(root, field));
    }
}
