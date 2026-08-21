namespace SapGuiAgent.Components;

/// <summary>Raised by a handler when the SAP GUI Scripting API genuinely cannot perform the
/// requested op. Caught at the ExecuteAsync boundary and turned into an ActionResult with
/// `unsupported_reason` set — never a silent no-op (spec §11 coverage honesty).</summary>
public sealed class UnsupportedOperationException : Exception
{
    public UnsupportedOperationException(string message) : base(message) { }
}
