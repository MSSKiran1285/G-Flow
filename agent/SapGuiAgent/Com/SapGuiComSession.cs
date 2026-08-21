using SapGuiAgent.Grpc;

namespace SapGuiAgent.Com;

/// <summary>Late-bound wrapper around one SAP GUI Scripting `GuiSession` COM object.
/// All calls against `_handle` must run on the session's own STA thread — callers get
/// there via the paired <see cref="StaThreadDispatcher"/> held by the connection manager;
/// this class itself assumes it is already being called from that thread.</summary>
public sealed class SapGuiComSession : IComSession
{
    private readonly ComHandle _handle;
    private readonly List<string> _okCodeHistory = new();

    public SapGuiComSession(object native)
    {
        _handle = new ComHandle(native);
    }

    public object Native => _handle.Target;

    public string Id => ComHandle.TryGet(() => _handle.GetString("Id"), "");

    // VERIFY-ON-TARGET: GuiSession.Busy
    public bool Busy => ComHandle.TryGet(() => _handle.GetBool("Busy"), false);

    public IComComponent Root => new SapGuiComComponent(_handle.Call("FindById", "wnd[0]")!);

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
            var native = _handle.Call("FindById", id);
            return native is null ? null : new SapGuiComComponent(native);
        }
        catch
        {
            return null;
        }
    }

    public ScreenContext CaptureContext()
    {
        var info = _handle.GetCom("Info"); // VERIFY-ON-TARGET: GuiSessionInfo member names below
        var context = new ScreenContext
        {
            SystemId = ComHandle.TryGet(() => info.GetString("SystemName"), ""),
            Client = ComHandle.TryGet(() => info.GetString("Client"), ""),
            User = ComHandle.TryGet(() => info.GetString("User"), ""),
            TransactionCode = ComHandle.TryGet(() => info.GetString("Transaction"), ""),
            Program = ComHandle.TryGet(() => info.GetString("Program"), ""),
            ScreenNumber = ComHandle.TryGet(() => info.Get("ScreenNumber")?.ToString() ?? "", ""),
            WindowTitle = ComHandle.TryGet(() => new ComHandle(Root.Native).GetString("Text"), ""),
        };
        var modals = ModalWindows;
        context.WindowCount = 1 + modals.Count;
        foreach (var modal in modals)
        {
            context.ModalStack.Add(ComHandle.TryGet(() => new ComHandle(modal.Native).GetString("Text"), ""));
        }
        return context;
    }

    public void SendVKey(int vkey)
    {
        // VERIFY-ON-TARGET: GuiFrameWindow.SendVKey(int)
        _handle.CallCom("FindById", "wnd[0]").Call("SendVKey", vkey);
        _okCodeHistory.Add($"VKey:{vkey}");
    }

    public IReadOnlyList<string> OkCodeHistory => _okCodeHistory;

    internal void RecordOkCode(string code) => _okCodeHistory.Add(code);
}
