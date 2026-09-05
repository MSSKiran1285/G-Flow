using System.Linq;
using Grpc.Core;
using SapGuiAgent.Com;
using SapGuiAgent.Components;
using SapGuiAgent.Native;
using SapGuiAgent.Scanning;

namespace SapGuiAgent.Grpc;

public sealed class UiAgentService : UiAgent.UiAgentBase
{
    private readonly SapGuiConnectionManager _connections;
    private readonly IScreenScanner _scanner;
    private readonly IComponentHandlerRegistry _registry;
    private readonly ScreenshotService _screenshots;

    public UiAgentService(
        SapGuiConnectionManager connections,
        IScreenScanner scanner,
        IComponentHandlerRegistry registry,
        ScreenshotService screenshots)
    {
        _connections = connections;
        _scanner = scanner;
        _registry = registry;
        _screenshots = screenshots;
    }

    public override Task<ConnectionList> ListConnections(ListConnectionsRequest request, ServerCallContext context) =>
        _connections.ListConnectionsAsync();

    public override Task<SessionHandle> OpenSession(OpenSessionRequest request, ServerCallContext context) =>
        _connections.OpenSessionAsync(request);

    public override Task<Ack> CloseSession(SessionHandle request, ServerCallContext context) =>
        _connections.CloseSessionAsync(request.SessionId);

    public override async Task<SessionInfo> GetSessionInfo(SessionHandle request, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        var ctx = await sta.RunAsync(session.CaptureContext);
        return new SessionInfo { SessionId = session.Id, Context = ctx };
    }

    public override async Task<ScreenSnapshot> ScanScreen(ScanRequest request, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        return await sta.RunAsync(() => _scanner.ScanAsync(session, request, context.CancellationToken).GetAwaiter().GetResult());
    }

    public override async Task<ActionResult> ExecuteAction(ActionRequest request, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        return await sta.RunAsync(() => RunAction(session, request, context.CancellationToken));
    }

    public override async Task ExecuteBatch(ActionBatch request, IServerStreamWriter<ActionResult> responseStream, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        foreach (var step in request.Steps)
        {
            var result = await sta.RunAsync(() => RunAction(session, step, context.CancellationToken));
            await responseStream.WriteAsync(result);
            if (request.FailFast && !result.Success)
            {
                break;
            }
        }
    }

    private ActionResult RunAction(SapGuiComSession session, ActionRequest request, CancellationToken ct)
    {
        var component = session.FindById(request.ComponentId);
        if (component is null)
        {
            return new ActionResult { Success = false, ErrorMessage = $"component '{request.ComponentId}' not found" };
        }
        var handler = _registry.Resolve(component.Type, component.SubType);
        return handler.ExecuteAsync(component, request, ct).GetAwaiter().GetResult();
    }

    public override Task<LocatorCandidates> ResolveLocator(LocatorRequest request, ServerCallContext context)
    {
        // Self-healing candidate scoring is core-side and lands in M5 (spec §7) — not faked here.
        throw new RpcException(new Status(StatusCode.Unimplemented, "ResolveLocator lands in M5 (see spec §7)"));
    }

    public override async Task Subscribe(SessionHandle request, IServerStreamWriter<UiEvent> responseStream, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        string? lastStatusText = null;
        while (!context.CancellationToken.IsCancellationRequested)
        {
            var message = await sta.RunAsync(() =>
            {
                var statusbar = session.FindById("wnd[0]/sbar"); // VERIFY-ON-TARGET: statusbar id
                return statusbar is null ? (StatusbarMessage?)null : StatusbarHandler.ReadMessage(statusbar.Native);
            });
            if (message is StatusbarMessage msg && msg.Text != lastStatusText)
            {
                lastStatusText = msg.Text;
                await responseStream.WriteAsync(new UiEvent
                {
                    SessionId = session.Id,
                    Type = UiEventType.StatusbarMessage,
                    Statusbar = msg,
                });
            }
            try
            {
                await Task.Delay(300, context.CancellationToken);
            }
            catch (TaskCanceledException)
            {
                break;
            }
        }
    }

    public override async Task StartElementPicker(SessionHandle request, IServerStreamWriter<PickedComponent> responseStream, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        var detector = new ClickEdgeDetector();
        ScreenSnapshot? cachedSnapshot = null;
        ScreenContext? cachedContext = null;

        while (!context.CancellationToken.IsCancellationRequested)
        {
            if (detector.TryDetectClick(out var x, out var y))
            {
                var (picked, caption, windowTitle) = await sta.RunAsync(() =>
                {
                    // Found live: a full root_id="*" rescan on every single click made the
                    // picker unusably slow on data-heavy screens (VA01's item overview table
                    // alone can take 20s+ to scan — hundreds of cells, each needing several
                    // late-bound COM round trips per property). A capture session is someone
                    // picking several fields off the SAME static screen, so the snapshot only
                    // needs refreshing when the screen actually changes — checked cheaply via
                    // GuiSessionInfo (tcode/screen/window count/modal titles), not a tree walk.
                    // Known tradeoff: scrolling a table without changing screen/tcode (e.g.
                    // paging its rows) goes undetected, so a click after a scroll can hit-test
                    // against stale row positions until something else invalidates the cache.
                    var currentContext = session.CaptureContext();
                    if (cachedSnapshot is null || !SameScreen(cachedContext, currentContext))
                    {
                        // root_id="*" so a click inside a modal popup (e.g. a completeness-check
                        // dialog) hit-tests correctly too, same as any other full-tree scan.
                        cachedSnapshot = _scanner
                            .ScanAsync(session, new ScanRequest { SessionId = session.Id, RootId = "*" }, context.CancellationToken)
                            .GetAwaiter().GetResult();
                        cachedContext = currentContext;
                    }
                    var hit = ComponentHitTester.Find(cachedSnapshot.Root, x, y);
                    var hitCaption = hit is null ? "" : ComponentHitTester.FindCaption(cachedSnapshot.Root, hit);
                    var hitWindowTitle = hit is null ? "" : ComponentHitTester.FindWindowTitle(cachedSnapshot.Root, hit);
                    return (hit, hitCaption, hitWindowTitle);
                });

                // null means the click landed outside this session's own SAP GUI window
                // entirely (e.g. in the browser) — silently ignored, not an error.
                if (picked is not null)
                {
                    await responseStream.WriteAsync(new PickedComponent
                    {
                        SessionId = session.Id,
                        ComponentId = picked.Id,
                        Type = picked.Type,
                        SubType = picked.SubType,
                        Family = picked.Family,
                        Name = picked.Name,
                        Text = picked.Text,
                        Tooltip = picked.Tooltip,
                        Caption = caption,
                        WindowTitle = windowTitle,
                    });
                }
            }

            try
            {
                await Task.Delay(40, context.CancellationToken);
            }
            catch (TaskCanceledException)
            {
                break;
            }
        }
    }

    /// <summary>Cheap enough to call on every click (a handful of GuiSessionInfo property
    /// reads, no tree walk) — used to decide whether the picker's cached snapshot is still
    /// good or the screen has actually moved on and needs a fresh (expensive) rescan.</summary>
    private static bool SameScreen(ScreenContext? cached, ScreenContext current)
    {
        if (cached is null)
        {
            return false;
        }
        return cached.TransactionCode == current.TransactionCode
            && cached.ScreenNumber == current.ScreenNumber
            && cached.WindowCount == current.WindowCount
            && cached.ModalStack.SequenceEqual(current.ModalStack);
    }

    public override async Task<ImageBlob> CaptureScreenshot(CaptureRequest request, ServerCallContext context)
    {
        var (session, sta) = RequireSession(request.SessionId);
        return await sta.RunAsync(() =>
        {
            var component = string.IsNullOrEmpty(request.ComponentId) ? session.Root : session.FindById(request.ComponentId);
            if (component is null)
            {
                throw new InvalidOperationException($"component '{request.ComponentId}' not found");
            }
            return _screenshots.Capture(component);
        });
    }

    public override Task<OkCodeHistory> GetOkCodeHistory(SessionHandle request, ServerCallContext context)
    {
        var (session, _) = RequireSession(request.SessionId);
        var history = new OkCodeHistory();
        history.OkCodes.AddRange(session.OkCodeHistory);
        return Task.FromResult(history);
    }

    private (SapGuiComSession Session, StaThreadDispatcher Sta) RequireSession(string sessionId)
    {
        if (!_connections.TryGetSession(sessionId, out var session, out var sta) || session is null || sta is null)
        {
            throw new RpcException(new Status(StatusCode.NotFound, $"unknown session '{sessionId}'"));
        }
        return (session, sta);
    }
}
