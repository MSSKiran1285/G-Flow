using System.Diagnostics;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;
using SapGuiAgent.Native;

namespace SapGuiAgent.Components;

/// <summary>Common timing/error-handling wrapper so individual handlers only implement the
/// actual op dispatch.</summary>
public abstract class ComponentHandlerBase : IComponentHandler
{
    public abstract ComponentFamily Family { get; }

    public abstract bool CanHandle(string sapType, string sapSubType);

    public virtual void EnrichSnapshot(IComComponent component, ComponentNode node, ScanDepthOptions depth)
    {
        // Most families need nothing beyond the common ComponentNode fields the scanner
        // already fills in. Override where family-specific detail applies (§4.1).
    }

    public async Task<ActionResult> ExecuteAsync(IComComponent component, ActionRequest request, CancellationToken ct)
    {
        var stopwatch = Stopwatch.StartNew();
        try
        {
            // Protobuf leaves an unset singular message field null (found live: a caller
            // that omits `params` entirely — e.g. GRID_SELECT_ROWS with no rows — crashed
            // every handler with a bare NullReferenceException instead of a clean result).
            request.Params ??= new ActionParams();


            // Universal across every family (GuiVComponent.SetFocus()) — handled here so
            // individual handlers don't each need a case for it.
            if (request.Op == ActionOp.SetFocus)
            {
                new ComHandle(component.Native).Call("SetFocus");
                return new ActionResult { Success = true, ElapsedMs = stopwatch.ElapsedMilliseconds };
            }

            // Universal across every family (GuiVComponent.Visualize(true)) — draws a
            // colored border around the component on the real, live screen. One-shot: SAP
            // clears it on the next redraw/interaction, so there's no matching "off" call.
            if (request.Op == ActionOp.Highlight)
            {
                new ComHandle(component.Native).Call("Visualize", true);
                return new ActionResult { Success = true, ElapsedMs = stopwatch.ElapsedMilliseconds };
            }

            // Last resort (spec §11): a real OS-level mouse click at the component's screen
            // coordinates, for controls that don't honor the equivalent scripting-API call
            // (found live: SAPLSBAL_DISPLAY's log-viewer ALV grid answers GetCellValue and
            // RowCount fine but ignores DoubleClick/SetCurrentCell — no scripting gesture
            // opens its long text). Gated on allow_fragile_fallback since it's a real click
            // on whatever is at those screen coordinates, not a scoped API call, and always
            // reports Fragile=true so callers know to treat the result skeptically.
            if (request.Op == ActionOp.CoordinateClickFallback)
            {
                if (!request.AllowFragileFallback)
                {
                    return new ActionResult
                    {
                        Success = false,
                        ErrorMessage = "COORDINATE_CLICK_FALLBACK requires allow_fragile_fallback=true",
                        ElapsedMs = stopwatch.ElapsedMilliseconds,
                    };
                }

                var native = new ComHandle(component.Native);
                var left = ComHandle.TryGet(() => native.GetInt("ScreenLeft"), 0);
                var top = ComHandle.TryGet(() => native.GetInt("ScreenTop"), 0);
                var width = ComHandle.TryGet(() => native.GetInt("Width"), 0);
                var height = ComHandle.TryGet(() => native.GetInt("Height"), 0);
                var extra = request.Params.Extra;
                var xOffset = extra.TryGetValue("x_offset", out var xs) && int.TryParse(xs, out var xv) ? xv : width / 2;
                var yOffset = extra.TryGetValue("y_offset", out var ys) && int.TryParse(ys, out var yv) ? yv : height / 2;
                var clickCount = extra.TryGetValue("click_count", out var cs) && int.TryParse(cs, out var cv) ? cv : 2;
                MouseInput.Click(left + xOffset, top + yOffset, clickCount);
                return new ActionResult { Success = true, Fragile = true, ElapsedMs = stopwatch.ElapsedMilliseconds };
            }

            var result = await ExecuteCoreAsync(component, request, ct);
            result.ElapsedMs = stopwatch.ElapsedMilliseconds;
            return result;
        }
        catch (UnsupportedOperationException ex)
        {
            return new ActionResult
            {
                Success = false,
                UnsupportedReason = ex.Message,
                ElapsedMs = stopwatch.ElapsedMilliseconds,
            };
        }
        catch (Exception ex)
        {
            // Type.InvokeMember (see ComHandle) wraps the real COM failure in a
            // TargetInvocationException — unwrap it so the message is actually useful.
            var real = ex is System.Reflection.TargetInvocationException { InnerException: { } inner } ? inner : ex;
            return new ActionResult
            {
                Success = false,
                ErrorMessage = real is System.Runtime.InteropServices.COMException com
                    ? $"{real.Message} (HRESULT 0x{com.HResult:X8})"
                    : real.Message,
                ElapsedMs = stopwatch.ElapsedMilliseconds,
            };
        }
    }

    protected abstract Task<ActionResult> ExecuteCoreAsync(IComComponent component, ActionRequest request, CancellationToken ct);

    protected static bool Compare(string actual, ActionParams p)
    {
        return p.Comparator switch
        {
            "contains" => actual.Contains(p.ExpectedValue),
            "regex" => System.Text.RegularExpressions.Regex.IsMatch(actual, p.ExpectedValue),
            "not_empty" => !string.IsNullOrEmpty(actual),
            "numeric_tolerance" => TryNumericTolerance(actual, p),
            "date_format" => actual == p.ExpectedValue, // VERIFY-ON-TARGET: date normalization TBD (§9 data domains)
            _ => actual == p.ExpectedValue, // "equals" and default
        };
    }

    private static bool TryNumericTolerance(string actual, ActionParams p)
    {
        if (!double.TryParse(actual, out var actualNum) || !double.TryParse(p.ExpectedValue, out var expectedNum))
        {
            return false;
        }
        return Math.Abs(actualNum - expectedNum) <= p.NumericTolerance;
    }
}
