using Microsoft.AspNetCore.Server.Kestrel.Core;
using SapGuiAgent.Com;
using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Scanning;

var builder = WebApplication.CreateBuilder(args);

var port = builder.Configuration.GetValue("Agent:Port", 50051);
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenLocalhost(port, listenOptions => listenOptions.Protocols = HttpProtocols.Http2);
});

builder.Services.AddGrpc();

var allowlist = builder.Configuration.GetSection("Agent:SystemAllowlist").Get<string[]>() ?? Array.Empty<string>();
builder.Services.AddSingleton(new SapGuiConnectionManager(allowlist));
builder.Services.AddSingleton<IComponentHandlerRegistry>(ComponentHandlerRegistry.CreateDefault());
builder.Services.AddSingleton<IScreenScanner, ScreenScanner>();
builder.Services.AddSingleton<ScreenshotService>();

var app = builder.Build();
app.MapGrpcService<UiAgentService>();
app.MapGet("/", () => "SapGuiAgent is running. Talk to it over gRPC (see proto/uiadapter.proto).");
app.Run();
