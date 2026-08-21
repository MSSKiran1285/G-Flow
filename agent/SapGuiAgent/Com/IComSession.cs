using System.Collections.Generic;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Com;

/// <summary>Wraps one SAP GUI Scripting COM session (GuiSession) behind a testable seam.</summary>
public interface IComSession
{
    string Id { get; }
    bool Busy { get; }
    IComComponent Root { get; }                        // wnd[0]
    IReadOnlyList<IComComponent> ModalWindows { get; }  // wnd[1..n], outermost first
    IComComponent? FindById(string id);
    ScreenContext CaptureContext();
    void SendVKey(int vkey);

    /// <summary>OK-codes sent on this session so far, oldest first. SAP GUI Scripting has
    /// no native history API for this — the agent tracks it itself as ok-codes are sent.
    /// Backs the GetOkCodeHistory rpc.</summary>
    IReadOnlyList<string> OkCodeHistory { get; }
}
