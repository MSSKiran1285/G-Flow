using System.Drawing;
using System.Drawing.Imaging;
using Google.Protobuf;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Scanning;

/// <summary>SAP GUI Scripting has no native "capture this component" API — screenshots are
/// taken at the OS/GDI level using the component's reported screen rect (spec §5:
/// "before/after screenshots").</summary>
public sealed class ScreenshotService
{
    public ImageBlob Capture(IComComponent component)
    {
        var native = new ComHandle(component.Native);
        var left = ComHandle.TryGet(() => native.GetInt("ScreenLeft"), 0);
        var top = ComHandle.TryGet(() => native.GetInt("ScreenTop"), 0);
        var width = Math.Max(1, ComHandle.TryGet(() => native.GetInt("Width"), 1));
        var height = Math.Max(1, ComHandle.TryGet(() => native.GetInt("Height"), 1));

        using var bitmap = new Bitmap(width, height);
        using var graphics = Graphics.FromImage(bitmap);
        graphics.CopyFromScreen(left, top, 0, 0, new Size(width, height));

        using var stream = new MemoryStream();
        bitmap.Save(stream, ImageFormat.Png);
        return new ImageBlob
        {
            Data = ByteString.CopyFrom(stream.ToArray()),
            Format = "png",
            Width = width,
            Height = height,
        };
    }
}
