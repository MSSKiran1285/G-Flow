using System.Security.Cryptography;
using System.Text;
using SapGuiAgent.Com;
using SapGuiAgent.Components;
using SapGuiAgent.Grpc;

namespace SapGuiAgent.Scanning;

/// <summary>Recursive tree walker producing a ScreenSnapshot (spec §4.1). M1 scope covers
/// dynpro controls; GuiShell deep introspection lands in M2 — until then, NotYetImplemented
/// handlers mark those subtrees `unmapped` rather than silently skipping them.</summary>
public sealed class ScreenScanner : IScreenScanner
{
    private readonly IComponentHandlerRegistry _registry;

    public ScreenScanner(IComponentHandlerRegistry registry)
    {
        _registry = registry;
    }

    public Task<ScreenSnapshot> ScanAsync(IComSession session, ScanRequest request, CancellationToken ct)
    {
        var context = session.CaptureContext();
        var unmapped = new List<string>();
        var hashInput = new StringBuilder();
        var depth = request.Depth ?? new ScanDepthOptions();

        var root = string.IsNullOrEmpty(request.RootId) || request.RootId is "wnd[0]" or "*"
            ? session.Root
            : session.FindById(request.RootId)
              ?? throw new InvalidOperationException($"component '{request.RootId}' not found");

        var rootNode = WalkNode(root, depth, unmapped, hashInput);

        if (request.IncludeModals || request.RootId == "*")
        {
            foreach (var modal in session.ModalWindows)
            {
                rootNode.Children.Add(WalkNode(modal, depth, unmapped, hashInput));
            }
        }

        var snapshot = new ScreenSnapshot
        {
            SessionId = session.Id,
            Context = context,
            Root = rootNode,
            SnapshotHash = ComputeHash(hashInput.ToString()),
        };
        snapshot.UnmappedComponentIds.AddRange(unmapped);
        return Task.FromResult(snapshot);
    }

    private ComponentNode WalkNode(IComComponent component, ScanDepthOptions depth, List<string> unmapped, StringBuilder hashInput)
    {
        var node = new ComponentNode
        {
            Id = component.Id,
            Type = component.Type,
            TypeAsNumber = component.TypeAsNumber,
            SubType = component.SubType,
            Family = ComponentFamilyClassifier.Classify(component.Type, component.SubType),
            Name = component.Name,
        };
        FillCommonProperties(component, node);

        hashInput.Append(node.Id).Append('|').Append(node.Type).Append('|')
            .Append(node.Text).Append('|').Append(node.Changeable).Append(';');

        var handler = _registry.Resolve(component.Type, component.SubType);
        handler.EnrichSnapshot(component, node, depth);
        if (node.Unmapped)
        {
            unmapped.Add(node.Id);
        }

        foreach (var child in component.Children)
        {
            node.Children.Add(WalkNode(child, depth, unmapped, hashInput));
        }

        return node;
    }

    private static void FillCommonProperties(IComComponent component, ComponentNode node)
    {
        var native = new ComHandle(component.Native);
        node.Text = ComHandle.TryGet(() => native.GetString("Text"), "");
        node.Tooltip = ComHandle.TryGet(() => native.GetString("Tooltip"), "");
        node.DefaultTooltip = ComHandle.TryGet(() => native.GetString("DefaultTooltip"), "");
        node.IconName = ComHandle.TryGet(() => native.GetString("IconName"), "");
        node.ScreenLeft = ComHandle.TryGet(() => native.GetInt("ScreenLeft"), 0);
        node.ScreenTop = ComHandle.TryGet(() => native.GetInt("ScreenTop"), 0);
        node.Width = ComHandle.TryGet(() => native.GetInt("Width"), 0);
        node.Height = ComHandle.TryGet(() => native.GetInt("Height"), 0);
        node.Changeable = ComHandle.TryGet(() => native.GetBool("Changeable"), false);
        node.Modified = ComHandle.TryGet(() => native.GetBool("Modified"), false);
        node.IsContainer = ComHandle.TryGet(() => native.GetBool("ContainerType"), false);
    }

    private static string ComputeHash(string canonical)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(canonical));
        return Convert.ToHexString(bytes);
    }
}
