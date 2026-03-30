import { useState } from "react"
import type { Thread } from "../types/profile"

interface TabBarProps {
  threads: Thread[]
  activeThreadId: string
  onSwitchThread: (threadId: string) => void
  onCreateThread: (label: string) => void
}

export function TabBar({ threads, activeThreadId, onSwitchThread, onCreateThread }: TabBarProps) {
  const [isCreating, setIsCreating] = useState(false)
  const [newLabel, setNewLabel] = useState("")

  const handleCreate = () => {
    if (newLabel.trim()) {
      onCreateThread(newLabel.trim())
      setNewLabel("")
      setIsCreating(false)
    }
  }

  return (
    <div className="flex items-center gap-1 px-4 py-2 border-b border-[#1e1e2e] bg-[#0a0a14] overflow-x-auto">
      {threads.map((t) => (
        <button
          key={t.threadId}
          onClick={() => onSwitchThread(t.threadId)}
          className={`px-3 py-1.5 rounded text-xs font-medium transition-colors shrink-0 cursor-pointer ${
            t.threadId === activeThreadId
              ? "bg-[#1a1a2e] text-white"
              : "text-[#666] hover:text-[#aaa] hover:bg-[#111120]"
          }`}
        >
          {t.label}
        </button>
      ))}
      {isCreating ? (
        <div className="flex items-center gap-1 shrink-0">
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate()
              if (e.key === "Escape") { setIsCreating(false); setNewLabel("") }
            }}
            placeholder="Thread name..."
            className="bg-[#111120] border border-[#2a2a3e] rounded px-2 py-1 text-xs text-white placeholder-[#555] focus:outline-none focus:border-[#3b82f6] w-32"
            autoFocus
          />
        </div>
      ) : (
        <button
          onClick={() => setIsCreating(true)}
          className="px-2 py-1.5 text-[#555] hover:text-[#888] text-xs cursor-pointer shrink-0"
          title="New thread"
        >
          +
        </button>
      )}
    </div>
  )
}
