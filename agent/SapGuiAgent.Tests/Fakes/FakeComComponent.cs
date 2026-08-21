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
    public dynamic Native => NativeObject;
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
