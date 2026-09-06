using System.Runtime.InteropServices;
using System.Text;

namespace SapGuiAgent.Native;

/// <summary>Brings the real live SAP GUI window to the foreground before a screen-coordinate
/// operation reads from it — screenshots (ScreenshotService.Capture) are a raw OS-level pixel
/// grab (Graphics.CopyFromScreen) at the component's reported ScreenLeft/Top, which happily
/// photographs whatever window is actually on top at those coordinates if the SAP window isn't
/// frontmost (e.g. another application's window, a browser popup, ...). Re-enumerates by
/// window class every call rather than caching a handle — this project's own "window position
/// drift" finding (docs/assumptions.md) is that a cached hwnd can go stale, not just move.</summary>
public static class WindowFocus
{
    private const string SapWindowClass = "SAP_FRONTEND_SESSION";

    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    private const int SW_RESTORE = 9;

    /// <summary>Swappable seam so tests can assert this was called without actually touching
    /// window Z-order on the machine running the test.</summary>
    public static Action BringSapWindowToForeground { get; set; } = BringSapWindowToForegroundReal;

    private static void BringSapWindowToForegroundReal()
    {
        var found = IntPtr.Zero;
        EnumWindows((hWnd, _) =>
        {
            if (!IsWindowVisible(hWnd))
            {
                return true;
            }
            var sb = new StringBuilder(256);
            GetClassName(hWnd, sb, sb.Capacity);
            if (sb.ToString() == SapWindowClass)
            {
                found = hWnd;
                return false; // stop enumerating
            }
            return true;
        }, IntPtr.Zero);

        if (found != IntPtr.Zero)
        {
            // Confirmed live: the whole SAP session (and SAP Logon) can end up minimized —
            // Windows parks a minimized window at (-32000,-32000) with a tiny placeholder
            // rect, which is exactly what a screen-coordinate screenshot would otherwise
            // silently capture. SetForegroundWindow alone does not un-minimize a window.
            if (IsIconic(found))
            {
                ShowWindow(found, SW_RESTORE);
            }
            SetForegroundWindow(found);
            // SetForegroundWindow's Z-order/compositor update isn't guaranteed synchronous —
            // a short wait avoids a screenshot racing ahead of the window actually raising.
            Thread.Sleep(150);
        }
    }
}
