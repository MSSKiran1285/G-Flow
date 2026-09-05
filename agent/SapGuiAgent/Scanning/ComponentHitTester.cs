using System.Text.RegularExpressions;
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

    private static readonly Regex PrefixSuffix = new(@"^([a-z]+)([A-Za-z0-9_].*)$", RegexOptions.Compiled);

    /// <summary>Finds the descriptive caption for a value-bearing control, trying two
    /// heuristics in order (confirmed against real screens this project has scanned —
    /// neither one alone covers every screen):
    /// 1. A sibling GuiLabel with the same id suffix, "lbl" prefix instead of the
    ///    control's own (e.g. ctxtVBAK-AUART's caption is lblVBAK-AUART's text) — cheap
    ///    and precise when SAP happens to name things this way.
    /// 2. The nearest caption-like control (a GuiLabel, or a non-editable GuiTextField
    ///    — some screens render captions as a plain read-only text field under an
    ///    unrelated program-variable name, e.g. VA01's "Order Type" caption for
    ///    VBAK-AUART is actually RV45A-TXT_AUART) positioned immediately to the left,
    ///    on the same row — the classic positional fallback every SAP screen actually
    ///    obeys, since captions are always laid out left of or above their field.
    /// Returns "" if the target is already its own caption (a label/button/menu) or
    /// nothing was found either way.</summary>
    public static string FindCaption(ComponentNode root, ComponentNode target)
    {
        if (target.Type == "GuiLabel")
        {
            return "";
        }
        var byId = FindCaptionById(root, target);
        return !string.IsNullOrEmpty(byId) ? byId : FindCaptionByPosition(root, target);
    }

    private static string FindCaptionById(ComponentNode root, ComponentNode target)
    {
        var lastSlash = target.Id.LastIndexOf('/');
        var parentPath = lastSlash >= 0 ? target.Id[..lastSlash] : "";
        var lastSegment = lastSlash >= 0 ? target.Id[(lastSlash + 1)..] : target.Id;

        // Table-control cells (e.g. "txtT030W-LTEXT[0,0]") don't reliably follow the
        // lbl-sibling convention — only the last path segment's own brackets count
        // here, not any earlier "wnd[0]"/"con[0]" segment further up the id.
        if (lastSegment.Contains('['))
        {
            return "";
        }

        var match = PrefixSuffix.Match(lastSegment);
        if (!match.Success)
        {
            return "";
        }
        var candidateId = $"{parentPath}/lbl{match.Groups[2].Value}";

        ComponentNode? found = null;
        void Walk(ComponentNode node)
        {
            if (found is not null)
            {
                return;
            }
            if (node.Type == "GuiLabel" && node.Id == candidateId)
            {
                found = node;
                return;
            }
            foreach (var child in node.Children)
            {
                Walk(child);
                if (found is not null)
                {
                    return;
                }
            }
        }

        Walk(root);
        return found?.Text ?? "";
    }

    private static bool IsCaptionLike(ComponentNode node) =>
        node.Type == "GuiLabel" || (node.Type == "GuiTextField" && !node.Changeable);

    private static string FindCaptionByPosition(ComponentNode root, ComponentNode target)
    {
        if (target.Width <= 0 || target.Height <= 0)
        {
            return "";
        }
        var targetCenterY = target.ScreenTop + target.Height / 2.0;
        var tolerance = target.Height / 2.0 + 4; // small slack for slightly misaligned rows

        ComponentNode? best = null;
        var bestLeft = int.MinValue;

        void Walk(ComponentNode node)
        {
            if (!ReferenceEquals(node, target) && IsCaptionLike(node) && node.Width > 0 && node.Height > 0)
            {
                var nodeCenterY = node.ScreenTop + node.Height / 2.0;
                if (Math.Abs(nodeCenterY - targetCenterY) <= tolerance &&
                    node.ScreenLeft + node.Width <= target.ScreenLeft &&
                    node.ScreenLeft > bestLeft)
                {
                    bestLeft = node.ScreenLeft;
                    best = node;
                }
            }
            foreach (var child in node.Children)
            {
                Walk(child);
            }
        }

        Walk(root);
        return best?.Text ?? "";
    }
}
