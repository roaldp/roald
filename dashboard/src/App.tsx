import { useState } from "react"
import { useProfile } from "./hooks/useProfile"
import { useConversation } from "./hooks/useConversation"
import { TopBar } from "./components/TopBar"
import { Sidebar } from "./components/Sidebar"
import { ConversationPanel } from "./components/ConversationPanel"
import { CalendarPanel } from "./components/CalendarPanel"
import { InputBar } from "./components/InputBar"

export default function App() {
  const { profile, isLoading, error } = useProfile()
  const [activeWsId, setActiveWsId] = useState<string | null>(null)

  const {
    messages,
    threads,
    activeThreadId,
    isLoading: convLoading,
    isSending,
    sendMessage,
    switchThread,
    createThread,
    approveTool,
    denyTool,
  } = useConversation(activeWsId)

  const handleWorkspaceClick = (wsId: string) => {
    setActiveWsId(wsId)
  }

  const handleShowOverview = () => {
    setActiveWsId(null)
  }

  const handleEventClick = (item: { relatedWsIds?: string[] }) => {
    if (item.relatedWsIds && item.relatedWsIds.length > 0) {
      setActiveWsId(item.relatedWsIds[0])
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0a12] text-[#555] text-sm">
        Loading...
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#0a0a12] text-[#888] text-sm gap-3">
        <div className="text-[#ef4444]">Failed to load profile</div>
        <div className="text-xs text-[#555]">{error || "profile.json not found"}</div>
        <div className="text-xs text-[#444] max-w-md text-center mt-2">
          Make sure profile.json exists in the project root. Run{" "}
          <code className="text-[#3b82f6]">python3 scripts/generate_profile.py</code> or create one manually.
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      <TopBar identity={profile.identity} sourceStatus={profile.sourceStatus} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          workspaces={profile.workspaces}
          activeWsId={activeWsId}
          threads={threads}
          activeThreadId={activeThreadId}
          onWorkspaceClick={handleWorkspaceClick}
          onThreadClick={switchThread}
          onShowOverview={handleShowOverview}
        />
        <ConversationPanel
          activeWsId={activeWsId}
          workspaces={profile.workspaces}
          messages={messages}
          threads={threads}
          activeThreadId={activeThreadId}
          isLoading={convLoading}
          isSending={isSending}
          onSwitchThread={switchThread}
          onCreateThread={createThread}
          onSelectWorkspace={handleWorkspaceClick}
          onApproveTool={approveTool}
          onDenyTool={denyTool}
        />
        <CalendarPanel
          agenda={profile.agenda}
          sourceStatus={profile.sourceStatus}
          onEventClick={handleEventClick}
        />
      </div>
      <InputBar
        placeholder={profile.inputPlaceholder}
        onSubmit={(text) => sendMessage(text)}
        disabled={!activeWsId}
        isSending={isSending}
      />
    </div>
  )
}
