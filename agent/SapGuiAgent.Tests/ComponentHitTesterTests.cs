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
}
