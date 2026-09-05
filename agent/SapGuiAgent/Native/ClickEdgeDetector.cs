namespace SapGuiAgent.Native;

/// <summary>Turns raw, continuously-polled pointer state (PointerWatch) into discrete
/// "a Ctrl+Click just happened" events — edge-triggered on the transition from "not
/// both held" to "both held", so one physical click fires exactly once no matter how
/// many poll iterations occur while the button stays down.</summary>
public sealed class ClickEdgeDetector
{
    private bool _wasDown;

    public bool TryDetectClick(out int x, out int y)
    {
        var down = PointerWatch.IsCtrlDown() && PointerWatch.IsLeftButtonDown();
        var fired = down && !_wasDown;
        _wasDown = down;

        if (fired)
        {
            (x, y) = PointerWatch.CursorPosition();
            return true;
        }

        (x, y) = (0, 0);
        return false;
    }
}
