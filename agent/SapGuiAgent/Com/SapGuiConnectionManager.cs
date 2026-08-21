using System.Collections.Concurrent;
using System.Runtime.InteropServices;
using SapGuiAgent.Grpc;
using ConnectionInfo = SapGuiAgent.Grpc.ConnectionInfo;

namespace SapGuiAgent.Com;

/// <summary>
/// Entry point into SAP GUI Scripting and owner of the session table. Guardrail (spec §5):
/// refuses to open or reuse a session whose system isn't on the configured allowlist.
/// </summary>
public sealed class SapGuiConnectionManager
{
    private readonly IReadOnlyList<string> _systemAllowlist;
    private readonly ConcurrentDictionary<string, (StaThreadDispatcher Sta, SapGuiComSession Session)> _sessions = new();

    public SapGuiConnectionManager(IEnumerable<string> systemAllowlist)
    {
        _systemAllowlist = systemAllowlist.ToList();
    }

    private static dynamic GetScriptingEngine()
    {
        // VERIFY-ON-TARGET: requires SAP Logon already running with a matching
        // `SAPGUI` moniker registered; scripting must be enabled client- and server-side.
        // Marshal.GetActiveObject isn't available on .NET Core/5+ (it wraps a Win32 API
        // that was never ported); Marshal.BindToMoniker is the supported equivalent for
        // reaching a running object by its registered moniker name.
        dynamic sapGuiAuto = Marshal.BindToMoniker("SAPGUI");
        return sapGuiAuto.GetScriptingEngine();
    }

    private bool IsAllowed(string? systemNameOrDescription)
    {
        if (_systemAllowlist.Count == 0) return true;
        if (string.IsNullOrEmpty(systemNameOrDescription)) return false;
        return _systemAllowlist.Any(a =>
            systemNameOrDescription.Contains(a, StringComparison.OrdinalIgnoreCase));
    }

    public Task<ConnectionList> ListConnectionsAsync()
    {
        return Task.Run(() =>
        {
            var result = new ConnectionList();
            dynamic engine = GetScriptingEngine();
            dynamic connections = engine.Connections; // VERIFY-ON-TARGET: GuiApplication.Connections
            int count = (int)connections.Count;
            for (var i = 0; i < count; i++)
            {
                dynamic connection = connections.ElementAt(i);
                var info = new ConnectionInfo
                {
                    ConnectionId = SapGuiComComponent.TryGet(() => (string)connection.Id, i.ToString()),
                    Description = SapGuiComComponent.TryGet(() => (string)connection.Description, ""),
                };
                int sessionCount = SapGuiComComponent.TryGet(() => (int)connection.Children.Count, 0);
                for (var s = 0; s < sessionCount; s++)
                {
                    info.SessionIds.Add(SapGuiComComponent.TryGet(
                        () => (string)connection.Children.ElementAt(s).Id, s.ToString()));
                }
                result.Connections.Add(info);
            }
            return result;
        });
    }

    public Task<SessionHandle> OpenSessionAsync(OpenSessionRequest request)
    {
        if (!IsAllowed(request.SystemDescription))
        {
            throw new InvalidOperationException(
                $"system '{request.SystemDescription}' is not on the configured allowlist");
        }

        var sta = new StaThreadDispatcher($"sap-session-{Guid.NewGuid():N}");
        return sta.RunAsync(() =>
        {
            dynamic engine = GetScriptingEngine();

            dynamic connection = string.IsNullOrEmpty(request.ConnectionId)
                // VERIFY-ON-TARGET: GuiApplication.OpenConnection(string description, bool sync)
                ? engine.OpenConnection(request.SystemDescription, true)
                : FindConnectionById(engine, request.ConnectionId);

            dynamic nativeSession = connection.Children.ElementAt(connection.Children.Count - 1);

            // Best-effort login: only fills fields that are actually present on the
            // logon screen (e.g. a fresh OpenConnection); reused/pre-authenticated
            // connections skip straight through. VERIFY-ON-TARGET.
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-MANDT", request.Client);
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-BNAME", request.User);
            TryFillLogonField(nativeSession, "wnd[0]/usr/pwdRSYST-BCODE", request.Password);
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-LANGU", request.Language);
            if (!string.IsNullOrEmpty(request.User))
            {
                try { nativeSession.FindById("wnd[0]").SendVKey(0); } catch { /* not on a logon screen */ }
            }

            var session = new SapGuiComSession(nativeSession);

            var systemName = SapGuiComComponent.TryGet(() => (string)nativeSession.Info.SystemName, "");
            if (!IsAllowed(systemName))
            {
                throw new InvalidOperationException(
                    $"system '{systemName}' is not on the configured allowlist");
            }

            _sessions[session.Id] = (sta, session);
            return new SessionHandle { SessionId = session.Id };
        });
    }

    private static void TryFillLogonField(dynamic session, string id, string value)
    {
        if (string.IsNullOrEmpty(value)) return;
        try
        {
            session.FindById(id).Text = value;
        }
        catch
        {
            // Field not present on the current screen (e.g. reusing an already logged-in
            // session) — not an error.
        }
    }

    private static dynamic FindConnectionById(dynamic engine, string connectionId)
    {
        dynamic connections = engine.Connections;
        int count = (int)connections.Count;
        for (var i = 0; i < count; i++)
        {
            dynamic connection = connections.ElementAt(i);
            if (SapGuiComComponent.TryGet(() => (string)connection.Id, "") == connectionId)
            {
                return connection;
            }
        }
        throw new InvalidOperationException($"no open connection with id '{connectionId}'");
    }

    public bool TryGetSession(string sessionId, out SapGuiComSession? session, out StaThreadDispatcher? sta)
    {
        if (_sessions.TryGetValue(sessionId, out var entry))
        {
            session = entry.Session;
            sta = entry.Sta;
            return true;
        }
        session = null;
        sta = null;
        return false;
    }

    public Task<Ack> CloseSessionAsync(string sessionId)
    {
        if (!_sessions.TryRemove(sessionId, out var entry))
        {
            return Task.FromResult(new Ack { Success = false, Message = $"unknown session '{sessionId}'" });
        }
        return entry.Sta.RunAsync(() =>
        {
            try
            {
                entry.Session.Native.FindById("wnd[0]").Close(); // VERIFY-ON-TARGET
            }
            catch
            {
                // Session may already be gone (e.g. server-side timeout) — closing is best-effort.
            }
            entry.Sta.Dispose();
            return new Ack { Success = true };
        });
    }
}
