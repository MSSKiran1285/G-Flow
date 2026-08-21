namespace SapGuiAgent.Com;

/// <summary>Late-bound wrapper around one SAP GUI Scripting `GuiComponent` COM object.
/// See docs/assumptions.md for why this uses `ComHandle`/`Type.InvokeMember` rather than
/// C#'s `dynamic` keyword.</summary>
public sealed class SapGuiComComponent : IComComponent
{
    private readonly ComHandle _handle;

    public SapGuiComComponent(object native)
    {
        _handle = new ComHandle(native);
    }

    public object Native => _handle.Target;

    public string Id => ComHandle.TryGet(() => _handle.GetString("Id"), "");
    public string Type => ComHandle.TryGet(() => _handle.GetString("Type"), "");
    public int TypeAsNumber => ComHandle.TryGet(() => _handle.GetInt("TypeAsNumber"), 0);

    // VERIFY-ON-TARGET: only GuiShell-family components expose SubType; others throw, and
    // we treat that as "no sub type" rather than an error.
    public string SubType => ComHandle.TryGet(() => _handle.GetString("SubType"), "");

    public string Name => ComHandle.TryGet(() => _handle.GetString("Name"), "");

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
                foreach (var child in _handle.Collection("Children"))
                {
                    list.Add(new SapGuiComComponent(child.Target));
                }
            }
            catch
            {
                // Leaf component — empty list.
            }
            return list;
        }
    }
}
