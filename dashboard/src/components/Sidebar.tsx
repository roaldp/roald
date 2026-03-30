import { WorkspaceItem } from "./WorkspaceItem"
import type { Workspace, Thread } from "../types/profile"

interface SidebarProps {
  workspaces: Workspace[]
  activeWsId: string | null
  threads: Thread[]
  activeThreadId: string
  onWorkspaceClick: (wsId: string) => void
  onThreadClick: (threadId: string) => void
  onShowOverview: () => void
}

export function Sidebar({ workspaces, activeWsId, threads, activeThreadId, onWorkspaceClick, onThreadClick, onShowOverview }: SidebarProps) {
  return (
    <div className="w-64 shrink-0 border-r border-[#1e1e2e] bg-[#0a0a14] flex flex-col overflow-hidden">
      <div className="px-3 pt-3 pb-2">
        <button
          onClick={onShowOverview}
          className={`w-full text-left px-3 py-2 rounded text-sm font-medium transition-colors cursor-pointer ${
            activeWsId === null
              ? "bg-[#1a1a2e] text-white"
              : "text-[#888] hover:bg-[#161625] hover:text-[#ccc]"
          }`}
        >
          Overview
        </button>
      </div>
      <div className="px-3 mb-2">
        <div className="text-[10px] text-[#444] uppercase tracking-wider px-3">Workspaces</div>
      </div>
      <div className="flex-1 overflow-y-auto px-1 pb-3">
        {workspaces.map((ws) => (
          <WorkspaceItem
            key={ws.id}
            workspace={ws}
            isActive={activeWsId === ws.id}
            threads={activeWsId === ws.id ? threads : []}
            activeThreadId={activeThreadId}
            onWorkspaceClick={onWorkspaceClick}
            onThreadClick={onThreadClick}
          />
        ))}
      </div>
    </div>
  )
}
