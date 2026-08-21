using System.Threading;
using System.Threading.Tasks;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

/// <summary>
/// One handler per §5 coverage-matrix family. The registry dispatches on the SAP-reported
/// (Type, SubType) pair — never on our own ComponentFamily enum, which only labels the
/// result after CanHandle has already matched.
/// </summary>
public interface IComponentHandler
{
    ComponentFamily Family { get; }

    bool CanHandle(string sapType, string sapSubType);

    /// <summary>Executes one uniform replay op against an already-resolved component.
    /// Locator resolution (incl. self-healing) happens in the Python core via ResolveLocator
    /// before this is ever called — this method only ever sees a concrete component.</summary>
    Task<ActionResult> ExecuteAsync(IComComponent component, ActionRequest request, CancellationToken ct);

    /// <summary>Called by the scanner while walking the tree to attach family-specific detail
    /// (ShellDetail / TableControlDetail / MenuDetail) onto a freshly-captured node. No-op for
    /// handlers with nothing to add beyond the common ComponentNode fields.</summary>
    void EnrichSnapshot(IComComponent component, ComponentNode node, ScanDepthOptions depth);
}

/// <summary>GuiTextField, GuiCTextField, GuiPasswordField.</summary>
public interface ITextInputHandler : IComponentHandler { }

/// <summary>GuiComboBox, GuiCheckBox, GuiRadioButton — select by key and by visible text.</summary>
public interface ISelectionHandler : IComponentHandler { }

/// <summary>GuiButton, GuiOkCodeField, GuiMenubar/GuiMenu (path-based), GuiToolbar.</summary>
public interface IActionHandler : IComponentHandler { }

/// <summary>GuiTabStrip/GuiTab, GuiSimpleContainer, GuiScrollContainer, GuiUserArea, GuiBox, GuiLabel.</summary>
public interface IStructureHandler : IComponentHandler { }

/// <summary>GuiMainWindow, GuiModalWindow, GuiFrameWindow.</summary>
public interface IWindowHandler : IComponentHandler { }

/// <summary>GuiStatusbar, incl. the message-pattern registry that auto-extracts created
/// document numbers into buffers.</summary>
public interface IStatusbarHandler : IComponentHandler { }

/// <summary>GuiTableControl — absolute-row get/set with scroll math, row select, column ops,
/// ConfigureLayout, find-row-by-predicate across pages.</summary>
public interface ITableControlHandler : IComponentHandler { }

/// <summary>GuiShell/GridView (ALV grid) — cell get/set by row + column-id, row/column
/// selection, toolbar/context-menu, checkbox/button/link cells.</summary>
public interface IAlvGridHandler : IComponentHandler { }

/// <summary>GuiShell/Tree (simple, list, column) — expand/collapse, node/item select,
/// checkbox items, link items, context menu.</summary>
public interface ITreeHandler : IComponentHandler { }

/// <summary>GuiShell/TextEdit — full text get/set, line ops, contains/regex verify.</summary>
public interface ITextShellHandler : IComponentHandler { }

/// <summary>Toolbar, HTMLViewer, Calendar, Splitter, TabStripInShell, Office/Picture/Chart
/// shells. Implements what the scripting API allows; where it doesn't, EnrichSnapshot marks
/// the node `unmapped`/`fragile` and ExecuteAsync raises UnsupportedOperation rather than
/// silently degrading (§11).</summary>
public interface IOtherShellHandler : IComponentHandler { }

/// <summary>Cross-cutting: SendVKey on any window, OK-code navigation, SAP Easy Access
/// favorites tree — anything reachable purely by keyboard, regardless of the focused
/// component's own family handler.</summary>
public interface ILegacyHandler : IComponentHandler { }

/// <summary>Resolves the right handler for a scanned or replayed component and is the single
/// place new families get wired in.</summary>
public interface IComponentHandlerRegistry
{
    IComponentHandler Resolve(string sapType, string sapSubType);
    void Register(IComponentHandler handler);
}

/// <summary>One entry in the popup-handler chain (§5 "popup discipline"): information popups,
/// multi-logon, "data will be lost", F4 helps, spool dialogs. Tried in registration order
/// against any unexpected wnd[n] before an action is allowed to fail.</summary>
public interface IPopupHandler
{
    string Name { get; }
    bool CanHandle(IComComponent modalWindow, ScreenContext context);
    Task<PopupHandled> HandleAsync(IComSession session, IComComponent modalWindow, CancellationToken ct);
}

/// <summary>Recursive tree walker that produces a ScreenSnapshot, delegating per-node
/// enrichment to the matching IComponentHandler (§4.1).</summary>
public interface IScreenScanner
{
    Task<ScreenSnapshot> ScanAsync(IComSession session, ScanRequest request, CancellationToken ct);
}
