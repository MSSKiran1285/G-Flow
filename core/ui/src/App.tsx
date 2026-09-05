import { useState } from "react";
import { ChainBuilder } from "./components/Chains/ChainBuilder";
import { ModulesPanel } from "./components/Modules/ModulesPanel";
import { ScriptsPanel } from "./components/Scripts/ScriptsPanel";
import { Sidebar } from "./components/Shell/Sidebar";
import { TopBar } from "./components/Shell/TopBar";

export type View = "modules" | "scripts" | "chains";

export function App() {
  const [view, setView] = useState<View>("scripts");

  return (
    <div className="app-shell">
      <Sidebar view={view} onChange={setView} />
      <div className="main-area">
        <TopBar view={view} />
        <div className="workspace-body">
          {view === "modules" && <ModulesPanel />}
          {view === "scripts" && <ScriptsPanel />}
          {view === "chains" && <ChainBuilder />}
        </div>
      </div>
    </div>
  );
}
