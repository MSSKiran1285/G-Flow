using System.Runtime.InteropServices;

namespace SapGuiAgent.Native;

/// <summary>OS-level mouse click simulation for COORDINATE_CLICK_FALLBACK (spec §11's
/// documented last resort — ActionOp.CoordinateClickFallback, always fragile=true). SAP GUI
/// Scripting has no generic "click here" API; some custom controls (e.g. the business
/// application log viewer's ALV grid, `SAPLSBAL_DISPLAY`) don't respond to the scripting-level
/// equivalents (GuiGridView.DoubleClick/SetCurrentCell) even though they answer other reads
/// correctly — this is the escape hatch for exactly that case. Uses the legacy `mouse_event`
/// API rather than `SendInput`: coordinates from GuiVComponent.ScreenLeft/Top are plain
/// absolute screen pixels (the same space ScreenshotService already uses via
/// Graphics.CopyFromScreen), and `SetCursorPos` + `mouse_event` consume that directly with no
/// virtual-desktop normalization needed.</summary>
public static class MouseInput
{
    private const int MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const int MOUSEEVENTF_LEFTUP = 0x0004;

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, nuint dwExtraInfo);

    /// <summary>Swappable seam so tests can assert click coordinates/count without actually
    /// moving the real mouse cursor on the machine running the test.</summary>
    public static Action<int, int, int> Click { get; set; } = PerformRealClick;

    private static void PerformRealClick(int x, int y, int clickCount)
    {
        SetCursorPos(x, y);
        for (var i = 0; i < clickCount; i++)
        {
            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0);
            mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
        }
    }
}
