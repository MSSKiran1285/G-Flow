using SapGuiAgent.Grpc;

namespace SapGuiAgent.Components;

public sealed class ComponentHandlerRegistry : IComponentHandlerRegistry
{
    private readonly List<IComponentHandler> _handlers = new();

    public static ComponentHandlerRegistry CreateDefault()
    {
        var registry = new ComponentHandlerRegistry();
        registry.Register(new TextInputHandler());
        registry.Register(new SelectionHandler());
        registry.Register(new ActionHandler());
        registry.Register(new StructureHandler());
        registry.Register(new WindowHandler());
        registry.Register(new StatusbarHandler());
        registry.Register(new AlvGridHandler());
        return registry;
    }

    public void Register(IComponentHandler handler) => _handlers.Add(handler);

    public IComponentHandler Resolve(string sapType, string sapSubType)
    {
        foreach (var handler in _handlers)
        {
            if (handler.CanHandle(sapType, sapSubType))
            {
                return handler;
            }
        }
        // No registered family handler — surface honestly rather than pretend support.
        return new NotYetImplementedHandler(ComponentFamilyClassifier.Classify(sapType, sapSubType));
    }
}
