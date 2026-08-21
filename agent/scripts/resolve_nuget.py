"""One-off offline NuGet mirror builder.

dotnet.exe's own HTTPS stack is blocked by this machine's network policy (confirmed:
PowerShell Invoke-WebRequest and `dotnet restore` both fail with connection resets against
api.nuget.org / dot.net, while curl.exe and Python's urllib -- both OpenSSL-based -- succeed
against the same URLs). So: resolve the dependency closure ourselves via urllib and populate
a local folder that `dotnet restore` can use as a NuGet source without any network access.

This is a heuristic resolver, not NuGet's real algorithm: for each dependency group in a
nuspec we take the UNION across all groups (over-fetch a few extra packages rather than
risk missing one to imprecise TFM matching), and for version conflicts we keep the max
version seen. Good enough for a one-time offline mirror of a known, small package set.
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\703393028\.nuget-offline-feed")
FEED_DIR.mkdir(parents=True, exist_ok=True)

ROOTS = [
    ("grpc.aspnetcore", "2.63.0"),
    ("google.protobuf", "3.27.0"),
    ("grpc.tools", "2.64.0"),
    ("system.drawing.common", "8.0.7"),
    ("microsoft.net.test.sdk", "17.11.1"),
    ("xunit", "2.9.2"),
    ("xunit.runner.visualstudio", "2.8.2"),
    ("moq", "4.20.72"),
    ("microsoft.netcore.app.ref", "8.0.30"),
    ("microsoft.aspnetcore.app.ref", "8.0.30"),
    ("microsoft.windowsdesktop.app.ref", "8.0.30"),
    ("microsoft.netcore.app.host.win-x64", "8.0.30"),
]

NS = {"n": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd",
      "n6": "http://schemas.microsoft.com/packaging/2011/08/nuspec.xsd",
      "n610": "http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd"}


def fetch(url: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def get_versions(pkg_id: str):
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_id}/index.json"
    import json
    return json.loads(fetch(url))["versions"]


def get_nuspec_deps(pkg_id: str, version: str):
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_id}/{version}/{pkg_id}.nuspec"
    try:
        xml_bytes = fetch(url)
    except Exception as e:
        print(f"  ! nuspec fetch failed for {pkg_id} {version}: {e}")
        return []
    root = ET.fromstring(xml_bytes)
    deps = []
    for ns_uri in [NS["n"], NS["n6"], NS["n610"], ""]:
        tag = f"{{{ns_uri}}}dependencies" if ns_uri else "dependencies"
        deps_el = root.find(f".//{tag}")
        if deps_el is not None:
            break
    else:
        return []
    for dep in deps_el.iter():
        if dep.tag.endswith("dependency"):
            did = dep.get("id")
            drange = dep.get("version") or ""
            if did:
                deps.append((did.lower(), drange))
    return deps


def parse_min_version(range_str: str) -> str:
    s = range_str.strip()
    if s.startswith("[") or s.startswith("("):
        s = s[1:]
    if "," in s:
        s = s.split(",")[0]
    if s.endswith("]") or s.endswith(")"):
        s = s[:-1]
    return s.strip()


def download_nupkg(pkg_id: str, version: str):
    dest = FEED_DIR / f"{pkg_id}.{version}.nupkg"
    if dest.exists():
        return
    url = f"https://api.nuget.org/v3-flatcontainer/{pkg_id}/{version}/{pkg_id}.{version}.nupkg"
    try:
        data = fetch(url, timeout=60)
    except Exception as e:
        print(f"  ! nupkg download failed for {pkg_id} {version}: {e}")
        return
    dest.write_bytes(data)
    print(f"  + {pkg_id} {version} ({len(data)} bytes)")


def resolve():
    resolved: dict[str, str] = {}
    queue = list(ROOTS)
    seen_pairs: set[tuple[str, str]] = set()

    while queue:
        pkg_id, version = queue.pop(0)
        pkg_id = pkg_id.lower()
        if (pkg_id, version) in seen_pairs:
            continue
        seen_pairs.add((pkg_id, version))

        current = resolved.get(pkg_id)
        if current is None or version_key(version) > version_key(current):
            resolved[pkg_id] = version

        print(f"resolving {pkg_id} {version} ...")
        for dep_id, dep_range in get_nuspec_deps(pkg_id, version):
            dep_version = parse_min_version(dep_range) or version
            queue.append((dep_id, dep_version))

    return resolved


def version_key(v: str):
    parts = []
    for p in v.split("-")[0].split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def main():
    resolved = resolve()
    print(f"\n{len(resolved)} packages resolved; downloading into {FEED_DIR} ...")
    for pkg_id, version in sorted(resolved.items()):
        download_nupkg(pkg_id, version)
    print("done.")


if __name__ == "__main__":
    main()
