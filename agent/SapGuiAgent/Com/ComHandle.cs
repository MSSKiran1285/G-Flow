using System.Reflection;

namespace SapGuiAgent.Com;

/// <summary>
/// Pure late-bound COM access via `Type.InvokeMember` (IDispatch::Invoke +
/// GetIDsOfNames) — deliberately NOT C#'s `dynamic` keyword.
///
/// Confirmed against a live system (see docs/assumptions.md "Live-system findings"):
/// `dynamic`'s DLR binder additionally calls `IDispatch::GetTypeInfo` to build a richer
/// binding, which threw `COMException 0x80029C4A (TYPE_E_CANTLOADLIBRARY)` against this
/// SAP GUI installation's COM registration — independent of process bitness (reproduced
/// under both x64 and x86). `Type.InvokeMember` only needs `IDispatch::Invoke`, which SAP
/// GUI Scripting supports fine, so every COM call in this agent goes through here instead.
/// </summary>
public readonly struct ComHandle
{
    private const BindingFlags GetFlags = BindingFlags.GetProperty | BindingFlags.Public | BindingFlags.Instance;
    private const BindingFlags SetFlags = BindingFlags.SetProperty | BindingFlags.Public | BindingFlags.Instance;
    private const BindingFlags CallFlags = BindingFlags.InvokeMethod | BindingFlags.Public | BindingFlags.Instance;

    public object Target { get; }

    public ComHandle(object target)
    {
        Target = target;
    }

    public object? Get(string name, params object?[] args) =>
        Target.GetType().InvokeMember(name, GetFlags, null, Target, args);

    public void Set(string name, object? value) =>
        Target.GetType().InvokeMember(name, SetFlags, null, Target, new[] { value });

    public object? Call(string name, params object?[] args) =>
        Target.GetType().InvokeMember(name, CallFlags, null, Target, args);

    public string GetString(string name) => Get(name) as string ?? "";
    public int GetInt(string name) => Convert.ToInt32(Get(name) ?? 0);
    public bool GetBool(string name) => Convert.ToBoolean(Get(name) ?? false);

    public ComHandle GetCom(string name) => new(Get(name)!);
    public ComHandle CallCom(string name, params object?[] args) => new(Call(name, args)!);

    /// <summary>Walks a SAP GUI Scripting collection (Count + 0-based ElementAt(int)) —
    /// the shape shared by GuiComponentCollection, GuiConnectionCollection, etc.</summary>
    public IEnumerable<ComHandle> Collection(string name)
    {
        var collection = GetCom(name);
        var count = collection.GetInt("Count");
        for (var i = 0; i < count; i++)
        {
            yield return collection.CallCom("ElementAt", i);
        }
    }

    public static T TryGet<T>(Func<T> getter, T fallback)
    {
        try
        {
            return getter();
        }
        catch
        {
            return fallback;
        }
    }
}
