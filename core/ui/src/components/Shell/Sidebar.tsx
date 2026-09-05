import { Blocks, GitBranch, ScrollText } from "lucide-react";
import type { View } from "../../App";

const NAV: { id: View; label: string; icon: typeof Blocks }[] = [
  { id: "modules", label: "Modules", icon: Blocks },
  { id: "scripts", label: "Scripts", icon: ScrollText },
  { id: "chains", label: "Chains", icon: GitBranch },
];

export function Sidebar({ view, onChange }: { view: View; onChange: (v: View) => void }) {
  return (
    <nav className="sidebar" aria-label="Workspaces">
      <div className="sidebar-brand">SapModelTest</div>
      {NAV.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className="nav-item"
          aria-current={view === id ? "page" : undefined}
          onClick={() => onChange(id)}
        >
          <Icon size={16} aria-hidden="true" />
          {label}
        </button>
      ))}
    </nav>
  );
}
