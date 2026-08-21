using SapGuiAgent.Grpc;

namespace SapGuiAgent.Com;

/// <summary>Late-bound wrapper around one SAP GUI Scripting `GuiSession` COM object.
/// All calls against `_native` must run on the session's own STA thread — callers get
/// there via the paired <see cref="StaThreadDispatcher"/> held by the connection manager;
/// this class itself assumes it is already being called from that thread.</summary>
public sealed class SapGuiComSession : IComSession
{
    private readonly dynamic _native;
    private readonly List<string> _okCodeHistory = new();

    public SapGuiComSession(dynamic native)
    {
        _native = native;
    }

    public dynamic Native => _native;

    public string Id => SapGuiComComponent.TryGet(() => (string)_native.Id, "");

    // VERIFY-ON-TARGET: GuiSession.Busy
    public bool Busy => SapGuiComComponent.TryGet(() => (bool)_native.Busy, false);

    public IComComponent Root => new SapGuiComComponent(_native.FindById("wnd[0]"));

    public IReadOnlyList<IComComponent> ModalWindows
    {
        get
        {
            var modals = new List<IComComponent>();
            // wnd[0] is the main window; wnd[1..n] are modals, outermost first.
            for (var i = 1; ; i++)
            {
                var found = FindById($"wnd[{i}]");
                if (found is null) break;
                modals.Add(found);
            }
            return modals;
        }
    }

    public IComComponent? FindById(string id)
    {
        try
        {
            return new SapGuiComComponent(_native.FindById(id));
        }
        catch
        {
            return null;
        }
    }

    public ScreenContext CaptureContext()
    {
        dynamic info = _native.Info; // VERIFY-ON-TARGET: GuiSessionInfo member names below
        var context = new ScreenContext
        {
            SystemId = SapGuiComComponent.TryGet(() => (string)info.SystemName, ""),
            Client = SapGuiComComponent.TryGet(() => (string)info.Client, ""),
            User = SapGuiComComponent.TryGet(() => (string)info.User, ""),
            TransactionCode = SapGuiComComponent.TryGet(() => (string)info.Transaction, ""),
            Program = SapGuiComComponent.TryGet(() => (string)info.Program, ""),
            ScreenNumber = SapGuiComComponent.TryGet(() => info.ScreenNumber.ToString(), ""),
            WindowTitle = SapGuiComComponent.TryGet(() => (string)Root.Native.Text, ""),
        };
        var modals = ModalWindows;
        context.WindowCount = 1 + modals.Count;
        foreach (var modal in modals)
        {
            context.ModalStack.Add(SapGuiComComponent.TryGet(() => (string)modal.Native.Text, ""));
        }
        return context;
    }

    public void SendVKey(int vkey)
    {
        // VERIFY-ON-TARGET: GuiFrameWindow.SendVKey(int)
        _native.FindById("wnd[0]").SendVKey(vkey);
        _okCodeHistory.Add($"VKey:{vkey}");
    }

    public IReadOnlyList<string> OkCodeHistory => _okCodeHistory;

    internal void RecordOkCode(string code) => _okCodeHistory.Add(code);
}
