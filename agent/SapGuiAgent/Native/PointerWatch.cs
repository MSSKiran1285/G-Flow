using System.Runtime.InteropServices;

namespace SapGuiAgent.Native;

/// <summary>OS-level pointer/keyboard state polling for the live element picker
/// (StartElementPicker). SAP GUI Scripting has no "tell me what's under the cursor"
/// API, and no "notify me on click" event either — so a Ctrl+Click gesture used to
/// pick a field is detected the same way COORDINATE_CLICK_FALLBACK performs one, just
/// in reverse: polling real OS input state (GetAsyncKeyState/GetCursorPos) rather than
/// driving it. Every member is a swappable static delegate (same seam as
/// MouseInput.Click) so tests can simulate a click sequence without touching the real
/// mouse/keyboard.</summary>
public static class PointerWatch
{
    private const int VK_CONTROL = 0x11;
    private const int VK_LBUTTON = 0x01;

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out Point lpPoint);

    [StructLayout(LayoutKind.Sequential)]
    private struct Point
    {
        public int X;
        public int Y;
    }

    public static Func<bool> IsCtrlDown { get; set; } = () => (GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0;

    public static Func<bool> IsLeftButtonDown { get; set; } = () => (GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0;

    public static Func<(int X, int Y)> CursorPosition { get; set; } = () =>
    {
        GetCursorPos(out var p);
        return (p.X, p.Y);
    };
}
