using SapGuiAgent.Grpc;

namespace SapGuiAgent.Scanning;

/// <summary>Pure point-in-rect hit-testing over an already-scanned ComponentNode tree —
/// what the live element picker (StartElementPicker) uses to turn a Ctrl+Click's screen
/// coordinates into the specific component the user pointed at. No COM/live-session
/// access here; this only ever runs against a ScreenSnapshot already produced by
/// ScreenScanner, so it's plain, fully unit-testable logic.</summary>
public static class ComponentHitTester
{
    /// <summary>Returns the smallest-area node (by ScreenLeft/Top/Width/Height) whose
    /// rect contains (x, y), preferring the most specific (usually deepest) match —
    /// e.g. a text field nested inside its container both contain the click point, but
    /// the field itself has the smaller rect and is what the user meant to pick. Nodes
    /// with zero width/height (menus, labels with no rendered box, etc.) never match.
    /// Returns null if nothing in the tree contains the point.</summary>
    public static ComponentNode? Find(ComponentNode root, int x, int y)
    {
        ComponentNode? best = null;
        var bestArea = long.MaxValue;

        void Walk(ComponentNode node)
        {
            if (Contains(node, x, y))
            {
                var area = (long)node.Width * node.Height;
                if (area < bestArea)
                {
                    bestArea = area;
                    best = node;
                }
            }
            foreach (var child in node.Children)
            {
                Walk(child);
            }
        }

        Walk(root);
        return best;
    }

    private static bool Contains(ComponentNode node, int x, int y) =>
        node.Width > 0 && node.Height > 0 &&
        x >= node.ScreenLeft && x < node.ScreenLeft + node.Width &&
        y >= node.ScreenTop && y < node.ScreenTop + node.Height;
}
