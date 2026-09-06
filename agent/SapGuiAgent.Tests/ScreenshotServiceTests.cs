using SapGuiAgent.Native;
using SapGuiAgent.Scanning;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class ScreenshotServiceTests
{
    /// <summary>The real bug this guards against: Capture() is a raw screen-coordinate
    /// pixel grab (Graphics.CopyFromScreen), which silently photographs whatever window is
    /// actually on top at that screen region if the SAP window isn't frontmost — confirmed
    /// live when the whole SAP session ended up minimized and every "screenshot" instead
    /// captured an unrelated browser window sitting on top. Capture must always try to
    /// raise the real SAP window first.</summary>
    [Fact]
    public void Capture_brings_the_sap_window_to_foreground_before_reading_the_screen_rect()
    {
        var original = WindowFocus.BringSapWindowToForeground;
        var called = false;
        WindowFocus.BringSapWindowToForeground = () => called = true;
        try
        {
            var native = new FakeGridViewNative { ScreenLeft = 0, ScreenTop = 0, Width = 1, Height = 1 };
            var component = new FakeComComponent { Id = "wnd[0]", Type = "GuiMainWindow", NativeObject = native };

            new ScreenshotService().Capture(component);

            Assert.True(called);
        }
        finally
        {
            WindowFocus.BringSapWindowToForeground = original;
        }
    }
}
