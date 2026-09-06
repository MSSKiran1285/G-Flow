import { SapConnectionPill } from "./SapConnectionPill";

const TITLES: Record<string, string> = {
  modules: "Object Library",
  scripts: "Scripts",
  chains: "Chains",
};

export function TopBar({ view }: { view: string }) {
  return (
    <div className="top-bar">
      <span className="breadcrumb">Workspace / {TITLES[view] ?? view}</span>
      <SapConnectionPill />
    </div>
  );
}
