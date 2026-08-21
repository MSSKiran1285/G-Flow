using System.Diagnostics;
using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

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
            return new ActionResult
            {
                Success = false,
                ErrorMessage = ex.Message,
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
