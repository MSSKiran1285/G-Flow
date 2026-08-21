using SapGuiAgent.Com;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Tests.Fakes;

public sealed class FakeComSession : IComSession
{
    private readonly Dictionary<string, IComComponent> _byId = new();

    public string Id { get; init; } = "fake-session";
    public bool Busy { get; init; }
    public required IComComponent Root { get; init; }
    public IReadOnlyList<IComComponent> ModalWindows { get; init; } = Array.Empty<IComComponent>();
    public ScreenContext Context { get; init; } = new();
    public List<string> OkCodeHistoryList { get; } = new();
    public IReadOnlyList<string> OkCodeHistory => OkCodeHistoryList;

    public void Index(IComComponent component)
    {
        _byId[component.Id] = component;
        foreach (var child in component.Children)
        {
            Index(child);
        }
    }

    public IComComponent? FindById(string id) => _byId.GetValueOrDefault(id);

    public ScreenContext CaptureContext() => Context;

    public void SendVKey(int vkey) => OkCodeHistoryList.Add($"VKey:{vkey}");
}
