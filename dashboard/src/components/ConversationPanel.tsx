import { useEffect, useRef } from "react"
import { ChatMessage } from "./ChatMessage"
import { TabBar } from "./TabBar"
import type { ChatMessage as ChatMessageType, Thread, Workspace, ToolCall } from "../types/profile"

interface ConversationPanelProps {
  activeWsId: string | null
  workspaces: Workspace[]
  messages: ChatMessageType[]
  threads: Thread[]
  activeThreadId: string
  isLoading: boolean
  isSending: boolean
  onSwitchThread: (threadId: string) => void
  onCreateThread: (label: string) => void
  onSelectWorkspace: (wsId: string) => void
  onApproveTool?: (msg: ChatMessageType, toolCall: ToolCall) => void
  onDenyTool?: (msg: ChatMessageType, toolCall: ToolCall) => void
}

function WorkspaceOverview({ workspaces, onSelect }: { workspaces: Workspace[]; onSelect: (id: string) => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="text-[#444] text-sm mb-6">Select a workspace to start</div>
      <div className="space-y-2 w-full max-w-sm">
        {workspaces.map((ws) => {
          const pending = ws.subtasks.reduce(
            (n, st) => n + st.feed.filter((f) => f.status !== "done").length, 0
          )
          return (
            <button
              key={ws.id}
              onClick={() => onSelect(ws.id)}
              className="w-full text-left px-4 py-3 rounded-lg border border-[#1e1e2e] bg-[#0d0d17] hover:border-[#2a2a3e] transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">{ws.icon}</span>
                <div className="flex-1">
                  <div className="text-sm text-white font-medium">{ws.name}</div>
                  <div className="text-xs text-[#555]">
                    {pending > 0 ? `${pending} items pending` : "All clear"}
                  </div>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-[#111120] border border-[#1e1e2e] rounded-xl px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-[#555]">
          <span className="flex gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[#555] animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="h-1.5 w-1.5 rounded-full bg-[#555] animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="h-1.5 w-1.5 rounded-full bg-[#555] animate-bounce" style={{ animationDelay: "300ms" }} />
          </span>
          Agent is thinking...
        </div>
      </div>
    </div>
  )
}

export function ConversationPanel({
  activeWsId,
  workspaces,
  messages,
  threads,
  activeThreadId,
  isLoading,
  isSending,
  onSwitchThread,
  onCreateThread,
  onSelectWorkspace,
  onApproveTool,
  onDenyTool,
}: ConversationPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages.length, isSending])

  if (!activeWsId) {
    return <WorkspaceOverview workspaces={workspaces} onSelect={onSelectWorkspace} />
  }

  const ws = workspaces.find((w) => w.id === activeWsId)

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <TabBar
        threads={threads}
        activeThreadId={activeThreadId}
        onSwitchThread={onSwitchThread}
        onCreateThread={onCreateThread}
      />
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-[#555] text-sm">
            Loading conversation...
          </div>
        ) : messages.length === 0 && !isSending ? (
          <div className="flex flex-col items-center justify-center py-16 text-[#444] text-sm">
            <span className="text-2xl mb-3">{ws?.icon}</span>
            <span>{ws?.name}</span>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onApproveTool={(tc) => onApproveTool?.(msg, tc)}
                onDenyTool={(tc) => onDenyTool?.(msg, tc)}
              />
            ))}
            {isSending && <ThinkingIndicator />}
          </>
        )}
      </div>
    </div>
  )
}
