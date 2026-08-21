using SapGuiAgent.Components;
using SapGuiAgent.Grpc;
using SapGuiAgent.Scanning;
using SapGuiAgent.Tests.Fakes;
using Xunit;

namespace SapGuiAgent.Tests;

public class ScreenScannerTests
{
    private static FakeComSession BuildSession(string orderTypeText)
    {
        var textField = new FakeComComponent
        {
            Id = "wnd[0]/usr/ctxtVBAK-AUART",
            Type = "GuiCTextField",
            Name = "VBAK-AUART",
            NativeObject = new FakeTextFieldNative { Text = orderTypeText },
        };
        var button = new FakeComComponent
        {
            Id = "wnd[0]/tbar[0]/btn[11]",
            Type = "GuiButton",
            Name = "btn[11]",
            NativeObject = new FakeButtonNative(),
        };
        var usr = new FakeComComponent { Id = "wnd[0]/usr", Type = "GuiContainerShell" };
        usr.ChildrenList.Add(textField);
        usr.ChildrenList.Add(button);

        var session = new FakeComSession { Root = usr, Context = new ScreenContext { TransactionCode = "VA01" } };
        session.Index(usr);
        return session;
    }

    [Fact]
    public async Task ScanAsync_builds_full_tree_with_family_assignment()
    {
        var session = BuildSession("OR");
        var scanner = new ScreenScanner(ComponentHandlerRegistry.CreateDefault());

        var snapshot = await scanner.ScanAsync(session, new ScanRequest { RootId = "wnd[0]/usr" }, CancellationToken.None);

        Assert.Equal("VA01", snapshot.Context.TransactionCode);
        Assert.Equal(2, snapshot.Root.Children.Count);
        Assert.Equal(ComponentFamily.FamilyTextInput, snapshot.Root.Children[0].Family);
        Assert.Equal(ComponentFamily.FamilyAction, snapshot.Root.Children[1].Family);
        Assert.Empty(snapshot.UnmappedComponentIds);
    }

    [Fact]
    public async Task ScanAsync_flags_unimplemented_families_as_unmapped_not_dropped()
    {
        var tableField = new FakeComComponent { Id = "wnd[0]/usr/tbl1", Type = "GuiTableControl" };
        var usr = new FakeComComponent { Id = "wnd[0]/usr", Type = "GuiContainerShell" };
        usr.ChildrenList.Add(tableField);
        var session = new FakeComSession { Root = usr };
        session.Index(usr);

        var scanner = new ScreenScanner(ComponentHandlerRegistry.CreateDefault());
        var snapshot = await scanner.ScanAsync(session, new ScanRequest { RootId = "wnd[0]/usr" }, CancellationToken.None);

        Assert.Single(snapshot.Root.Children);
        Assert.Contains("wnd[0]/usr/tbl1", snapshot.UnmappedComponentIds);
    }

    [Fact]
    public async Task ScanAsync_hash_is_stable_for_identical_screens_and_changes_when_a_value_changes()
    {
        var scanner = new ScreenScanner(ComponentHandlerRegistry.CreateDefault());

        var snapshotA = await scanner.ScanAsync(BuildSession("OR"), new ScanRequest { RootId = "wnd[0]/usr" }, CancellationToken.None);
        var snapshotB = await scanner.ScanAsync(BuildSession("OR"), new ScanRequest { RootId = "wnd[0]/usr" }, CancellationToken.None);
        var snapshotC = await scanner.ScanAsync(BuildSession("TA"), new ScanRequest { RootId = "wnd[0]/usr" }, CancellationToken.None);

        Assert.Equal(snapshotA.SnapshotHash, snapshotB.SnapshotHash);
        Assert.NotEqual(snapshotA.SnapshotHash, snapshotC.SnapshotHash);
    }
}
