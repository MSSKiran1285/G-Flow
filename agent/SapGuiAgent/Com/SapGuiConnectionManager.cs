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

    private static ComHandle GetScriptingEngine()
    {
        // VERIFY-ON-TARGET: requires SAP Logon already running with a matching
        // `SAPGUI` moniker registered; scripting must be enabled client- and server-side.
        // Marshal.GetActiveObject isn't available on .NET Core/5+ (it wraps a Win32 API
        // that was never ported); Marshal.BindToMoniker is the supported equivalent for
        // reaching a running object by its registered moniker name.
        var sapGuiAuto = new ComHandle(Marshal.BindToMoniker("SAPGUI"));
        return sapGuiAuto.CallCom("GetScriptingEngine");
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
            var engine = GetScriptingEngine();
            foreach (var connection in engine.Collection("Connections")) // VERIFY-ON-TARGET: GuiApplication.Connections
            {
                var info = new ConnectionInfo
                {
                    ConnectionId = ComHandle.TryGet(() => connection.GetString("Id"), ""),
                    Description = ComHandle.TryGet(() => connection.GetString("Description"), ""),
                };
                foreach (var session in ComHandle.TryGet(() => connection.Collection("Children"), Enumerable.Empty<ComHandle>()))
                {
                    info.SessionIds.Add(ComHandle.TryGet(() => session.GetString("Id"), ""));
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
            var engine = GetScriptingEngine();

            var connection = string.IsNullOrEmpty(request.ConnectionId)
                // VERIFY-ON-TARGET: GuiApplication.OpenConnection(string description, bool sync)
                ? engine.CallCom("OpenConnection", request.SystemDescription, true)
                : FindConnectionById(engine, request.ConnectionId);

            var sessions = connection.Collection("Children").ToList();
            var nativeSession = sessions[^1];

            // Best-effort login: only fills fields that are actually present on the
            // logon screen (e.g. a fresh OpenConnection); reused/pre-authenticated
            // connections skip straight through. VERIFY-ON-TARGET.
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-MANDT", request.Client);
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-BNAME", request.User);
            TryFillLogonField(nativeSession, "wnd[0]/usr/pwdRSYST-BCODE", request.Password);
            TryFillLogonField(nativeSession, "wnd[0]/usr/txtRSYST-LANGU", request.Language);
            if (!string.IsNullOrEmpty(request.User))
            {
                try { nativeSession.CallCom("FindById", "wnd[0]").Call("SendVKey", 0); } catch { /* not on a logon screen */ }
            }

            var session = new SapGuiComSession(nativeSession.Target);

            var systemName = ComHandle.TryGet(() => nativeSession.GetCom("Info").GetString("SystemName"), "");
            if (!IsAllowed(systemName))
            {
                throw new InvalidOperationException(
                    $"system '{systemName}' is not on the configured allowlist");
            }

            _sessions[session.Id] = (sta, session);
            return new SessionHandle { SessionId = session.Id };
        });
    }

    private static void TryFillLogonField(ComHandle session, string id, string value)
    {
        if (string.IsNullOrEmpty(value)) return;
        try
        {
            session.CallCom("FindById", id).Set("Text", value);
        }
        catch
        {
            // Field not present on the current screen (e.g. reusing an already logged-in
            // session) — not an error.
        }
    }

    private static ComHandle FindConnectionById(ComHandle engine, string connectionId)
    {
        foreach (var connection in engine.Collection("Connections"))
        {
            if (ComHandle.TryGet(() => connection.GetString("Id"), "") == connectionId)
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
                new ComHandle(entry.Session.Native).CallCom("FindById", "wnd[0]").Call("Close"); // VERIFY-ON-TARGET
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
