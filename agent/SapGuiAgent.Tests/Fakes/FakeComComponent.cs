using SapGuiAgent.Com;

namespace SapGuiAgent.Tests.Fakes;

/// <summary>Test double for IComComponent — no COM involved. `NativeObject` can be any
/// plain CLR object; dynamic dispatch works against its public members the same way it
/// would against a real COM IDispatch object, so handler code under test doesn't need to
/// know the difference.</summary>
public sealed class FakeComComponent : IComComponent
{
    public string Id { get; init; } = "";
    public string Type { get; init; } = "";
    public int TypeAsNumber { get; init; }
    public string SubType { get; init; } = "";
    public string Name { get; init; } = "";
    public List<IComComponent> ChildrenList { get; } = new();
    public IReadOnlyList<IComComponent> Children => ChildrenList;
    public object NativeObject { get; set; } = new();
    public object Native => NativeObject;
}

public sealed class FakeTextFieldNative
{
    public string Text { get; set; } = "";
}

public sealed class FakeButtonNative
{
    public bool Pressed { get; private set; }
    public void Press() => Pressed = true;
}

public sealed class FakeCheckBoxNative
{
    public bool Selected { get; set; }
}

public sealed class FakeStringCollection
{
    private readonly List<string> _items = new();
    public int Count => _items.Count;
    public string ElementAt(int i) => _items[i];
    public void Add(string s) => _items.Add(s);
}

public sealed class FakeGridViewNative
{
    public int RowCount { get; set; }
    public int VisibleRowCount { get; set; }
    public FakeStringCollection ColumnOrder { get; } = new();
    public int FirstVisibleRow { get; set; }
    public Dictionary<(int Row, string ColumnId), string> Cells { get; } = new();

    public string GetCellValue(int row, string columnId) =>
        Cells.TryGetValue((row, columnId), out var value) ? value : "";
}
