using SapGuiAgent.Native;
using Xunit;

namespace SapGuiAgent.Tests;

public class ClickEdgeDetectorTests
{
    private static Action Stub(bool ctrlDown, bool leftDown, (int X, int Y) pos)
    {
        var originalCtrl = PointerWatch.IsCtrlDown;
        var originalLeft = PointerWatch.IsLeftButtonDown;
        var originalPos = PointerWatch.CursorPosition;
        PointerWatch.IsCtrlDown = () => ctrlDown;
        PointerWatch.IsLeftButtonDown = () => leftDown;
        PointerWatch.CursorPosition = () => pos;
        return () =>
        {
            PointerWatch.IsCtrlDown = originalCtrl;
            PointerWatch.IsLeftButtonDown = originalLeft;
            PointerWatch.CursorPosition = originalPos;
        };
    }

    [Fact]
    public void TryDetectClick_fires_once_on_the_down_transition()
    {
        var restore = Stub(ctrlDown: false, leftDown: false, pos: (0, 0));
        try
        {
            var detector = new ClickEdgeDetector();
            Assert.False(detector.TryDetectClick(out _, out _));

            PointerWatch.IsCtrlDown = () => true;
            PointerWatch.IsLeftButtonDown = () => true;
            PointerWatch.CursorPosition = () => (120, 210);

            Assert.True(detector.TryDetectClick(out var x, out var y));
            Assert.Equal(120, x);
            Assert.Equal(210, y);
        }
        finally
        {
            restore();
        }
    }

    [Fact]
    public void TryDetectClick_does_not_refire_while_the_button_stays_held()
    {
        var restore = Stub(ctrlDown: true, leftDown: true, pos: (50, 60));
        try
        {
            var detector = new ClickEdgeDetector();
            Assert.True(detector.TryDetectClick(out _, out _));
            Assert.False(detector.TryDetectClick(out _, out _));
            Assert.False(detector.TryDetectClick(out _, out _));
        }
        finally
        {
            restore();
        }
    }

    [Fact]
    public void TryDetectClick_requires_both_ctrl_and_left_button_down()
    {
        var restore = Stub(ctrlDown: true, leftDown: false, pos: (1, 1));
        try
        {
            var detector = new ClickEdgeDetector();
            Assert.False(detector.TryDetectClick(out _, out _));
        }
        finally
        {
            restore();
        }
    }

    [Fact]
    public void TryDetectClick_fires_again_after_a_release_and_new_press()
    {
        var restore = Stub(ctrlDown: true, leftDown: true, pos: (1, 1));
        try
        {
            var detector = new ClickEdgeDetector();
            Assert.True(detector.TryDetectClick(out _, out _));

            PointerWatch.IsLeftButtonDown = () => false;
            Assert.False(detector.TryDetectClick(out _, out _));

            PointerWatch.IsLeftButtonDown = () => true;
            Assert.True(detector.TryDetectClick(out _, out _));
        }
        finally
        {
            restore();
        }
    }
}
