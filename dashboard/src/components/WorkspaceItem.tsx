import { useState } from "react"
import { SubtaskDot } from "./SubtaskDot"
import type { Workspace, Thread } from "../types/profile"

interface WorkspaceItemProps {
  workspace: Workspace
  isActive: boolean
  threads: Thread[]
  activeThreadId: string
  onWorkspaceClick: (wsId: string) => void
  onThreadClick: (threadId: string) => void
}

export function WorkspaceItem({ workspace, isActive, threads, activeThreadId, onWorkspaceClick, onThreadClick }: WorkspaceItemProps) {
  const [expanded, setExpanded] = useState(true)

  // Derive overall workspace health from subtasks
  const worstLight = workspace.subtasks.reduce<string>((worst, st) => {
    if (st.light === "red") return "red"
    if (st.light === "yellow" && worst !== "red") return "yellow"
    return worst
  }, "green")

  return (
    <div className="mb-1">
      <button
        onClick={() => {
          onWorkspaceClick(workspace.id)
          setExpanded(true)
        }}
        className={`flex items-center gap-2 w-full px-3 py-2 text-left text-sm rounded transition-colors cursor-pointer ${
          isActive ? "bg-[#161625]" : "hover:bg-[#161625]"
        }`}
      >
        <span className="text-base">{workspace.icon}</span>
        <span className={`font-medium flex-1 ${isActive ? "text-white" : "text-[#ccc]"}`}>
          {workspace.name}
        </span>
        {worstLight !== "green" && (
          <SubtaskDot light={worstLight as "green" | "yellow" | "red"} />
        )}
      </button>
      {expanded && isActive && threads.length > 1 && (
        <div className="ml-4 border-l border-[#1e1e2e]">
          {threads.map((t) => (
            <button
              key={t.threadId}
              onClick={() => onThreadClick(t.threadId)}
              className={`flex items-center gap-2 w-full px-3 py-1.5 text-left text-xs rounded transition-colors cursor-pointer ${
                activeThreadId === t.threadId ? "bg-[#161625] text-white" : "text-[#999] hover:bg-[#161625]"
              }`}
            >
              <span className="truncate flex-1">{t.label}</span>
              {t.messageCount > 0 && (
                <span className="text-[10px] text-[#555]">{t.messageCount}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
