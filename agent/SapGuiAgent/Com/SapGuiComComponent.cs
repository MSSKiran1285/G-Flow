namespace SapGuiAgent.Com;

/// <summary>Late-bound wrapper around one SAP GUI Scripting `GuiComponent` COM object.
/// See docs/assumptions.md for why this is dynamic rather than an early-bound interop type.</summary>
public sealed class SapGuiComComponent : IComComponent
{
    private readonly dynamic _native;

    public SapGuiComComponent(dynamic native)
    {
        _native = native;
    }

    public dynamic Native => _native;

    public string Id => TryGet(() => (string)_native.Id, "");
    public string Type => TryGet(() => (string)_native.Type, "");
    public int TypeAsNumber => TryGet(() => (int)_native.TypeAsNumber, 0);

    // VERIFY-ON-TARGET: only GuiShell-family components expose SubType; others throw, and
    // we treat that as "no sub type" rather than an error.
    public string SubType => TryGet(() => (string)_native.SubType, "");

    public string Name => TryGet(() => (string)_native.Name, "");

    public IReadOnlyList<IComComponent> Children
    {
        get
        {
            var list = new List<IComComponent>();
            try
            {
                // VERIFY-ON-TARGET: GuiVComponent/GuiContainer expose Children with
                // Count + ElementAt(int); a true leaf (e.g. GuiTextField) throws here,
                // which we treat as "no children" rather than an error.
                dynamic children = _native.Children;
                int count = (int)children.Count;
                for (int i = 0; i < count; i++)
                {
                    list.Add(new SapGuiComComponent(children.ElementAt(i)));
                }
            }
            catch
            {
                // Leaf component — empty list.
            }
            return list;
        }
    }

    internal static T TryGet<T>(Func<T> getter, T fallback)
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
