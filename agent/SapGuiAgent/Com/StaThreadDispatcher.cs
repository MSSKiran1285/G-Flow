using System.Collections.Concurrent;

namespace SapGuiAgent.Com;

/// <summary>
/// SAP GUI Scripting COM objects are apartment-threaded: every call against a given
/// GuiSession must run on the same STA thread that created it. This dispatcher owns one
/// dedicated STA thread and a work queue, so callers on the gRPC threadpool can safely
/// marshal COM calls onto it (spec §2 rationale: "sane STA/COM apartment threading for
/// parallel sessions"). One instance per session.
/// </summary>
public sealed class StaThreadDispatcher : IDisposable
{
    private readonly BlockingCollection<Action> _queue = new();
    private readonly Thread _thread;

    public StaThreadDispatcher(string name)
    {
        _thread = new Thread(RunLoop) { IsBackground = true, Name = name };
        _thread.SetApartmentState(ApartmentState.STA);
        _thread.Start();
    }

    private void RunLoop()
    {
        foreach (var work in _queue.GetConsumingEnumerable())
        {
            work();
        }
    }

    public Task<T> RunAsync<T>(Func<T> func)
    {
        var tcs = new TaskCompletionSource<T>(TaskCreationOptions.RunContinuationsAsynchronously);
        _queue.Add(() =>
        {
            try
            {
                tcs.SetResult(func());
            }
            catch (Exception ex)
            {
                tcs.SetException(ex);
            }
        });
        return tcs.Task;
    }

    public Task RunAsync(Action action) => RunAsync<object?>(() =>
    {
        action();
        return null;
    });

    public void Dispose()
    {
        _queue.CompleteAdding();
    }
}
