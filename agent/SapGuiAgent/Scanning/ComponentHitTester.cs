using System.Collections.Generic;
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

    /// <summary>Controls whose own .Text (or .Tooltip, for icon-only buttons) already IS the
    /// descriptive English label — a button reading "Save" or a tab reading "Item overview"
    /// needs no separate caption lookup; searching for one elsewhere only finds nothing or,
    /// worse, an unrelated neighbor.</summary>
    private static readonly HashSet<string> SelfCaptionedTypes = new()
    {
        "GuiButton", "GuiTab", "GuiRadioButton", "GuiCheckBox", "GuiMenu",
    };

    /// <summary>Finds the descriptive caption for a value-bearing control, trying heuristics
    /// in order (confirmed against real screens this project has scanned — no single one
    /// covers every case):
    /// 0. Self-captioned controls (buttons, tabs, radio buttons, checkboxes, menu entries)
    ///    — their own Text/Tooltip already is the caption.
    /// 1. A sibling GuiLabel with the same id suffix, "lbl" prefix instead of the
    ///    control's own (e.g. ctxtVBAK-AUART's caption is lblVBAK-AUART's text) — cheap
    ///    and precise when SAP happens to name things this way.
    /// 2. For a classic table-control cell (id ends "...[col,row]"), the cell's column
    ///    title (e.g. RV45A-MABNR's caption is its table's "Material" column header) —
    ///    positional/sibling heuristics don't apply here since the header row sits above
    ///    every data row, not aligned with any one of them.
    /// 3. The nearest caption-like control (a GuiLabel, or a non-editable GuiTextField
    ///    — some screens render captions as a plain read-only text field under an
    ///    unrelated program-variable name, e.g. VA01's "Order Type" caption for
    ///    VBAK-AUART is actually RV45A-TXT_AUART) positioned immediately to the left,
    ///    on the same row — the classic positional fallback every SAP screen actually
    ///    obeys, since captions are always laid out left of or above their field.
    /// Returns "" if the target is already its own caption (a label) or nothing was found
    /// by any heuristic.</summary>
    public static string FindCaption(ComponentNode root, ComponentNode target)
    {
        if (target.Type == "GuiLabel")
        {
            return "";
        }
        if (SelfCaptionedTypes.Contains(target.Type))
        {
            return !string.IsNullOrEmpty(target.Text) ? target.Text : target.Tooltip;
        }
        var byId = FindCaptionById(root, target);
        if (!string.IsNullOrEmpty(byId))
        {
            return byId;
        }
        var byColumn = FindCaptionByColumn(root, target);
        if (!string.IsNullOrEmpty(byColumn))
        {
            return byColumn;
        }
        return FindCaptionByPosition(root, target);
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

    /// <summary>A classic GuiTableControl cell's id ends "...[col,row]" (confirmed live on
    /// VA01's item overview table: ctxtRV45A-MABNR[1,3] is column 1, row 3). Column index
    /// doubles as the lookup key into the containing table's TableDetail.Columns, populated
    /// at scan time by TableControlHandler from GuiTableControl.Columns — same left-to-right
    /// display order, so no separate technical-name matching is needed.</summary>
    private static string FindCaptionByColumn(ComponentNode root, ComponentNode target)
    {
        var lastSlash = target.Id.LastIndexOf('/');
        var lastSegment = lastSlash >= 0 ? target.Id[(lastSlash + 1)..] : target.Id;
        var bracket = lastSegment.IndexOf('[');
        if (bracket < 0)
        {
            return "";
        }
        var inside = lastSegment[(bracket + 1)..].TrimEnd(']');
        var parts = inside.Split(',');
        if (parts.Length != 2 || !int.TryParse(parts[0], out var columnIndex))
        {
            return "";
        }

        var containingTable = FindContainingTable(root, target, null);
        var columns = containingTable?.TableDetail?.Columns;
        if (columns is null || columnIndex < 0 || columnIndex >= columns.Count)
        {
            return "";
        }
        return columns[columnIndex].Title;
    }

    private static ComponentNode? FindContainingTable(ComponentNode node, ComponentNode target, ComponentNode? nearestTable)
    {
        var thisTable = node.Type == "GuiTableControl" ? node : nearestTable;
        if (ReferenceEquals(node, target))
        {
            return thisTable;
        }
        foreach (var child in node.Children)
        {
            var found = FindContainingTable(child, target, thisTable);
            if (found is not null)
            {
                return found;
            }
        }
        return null;
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
