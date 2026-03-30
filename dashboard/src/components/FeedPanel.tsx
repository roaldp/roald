import { FeedEntry } from "./FeedEntry"
import type { FeedEntry as FeedEntryType, Workspace } from "../types/profile"

const TRIAGE_VISIBLE = 7

interface FeedPanelProps {
  workspaces: Workspace[]
  activeWsId: string | null
  activeSubtaskId: string | null
  onApprove: (wsId: string, subtaskId: string, entry: FeedEntryType) => void
  onDismiss: (wsId: string, subtaskId: string, entryId: string) => void
  onRedirect: (wsId: string, subtaskId: string, entryId: string, message: string) => void
}

function getAttentionFeed(workspaces: Workspace[]): Array<{ wsId: string; subtaskId: string; entry: FeedEntryType; wsName: string; subtaskName: string }> {
  const items: Array<{ wsId: string; subtaskId: string; entry: FeedEntryType; wsName: string; subtaskName: string }> = []
  for (const ws of workspaces) {
    for (const st of ws.subtasks) {
      for (const fe of st.feed) {
        if (fe.status === "urgent" || fe.status === "question" || fe.status === "pending") {
          items.push({ wsId: ws.id, subtaskId: st.id, entry: fe, wsName: ws.name, subtaskName: st.name })
        }
      }
    }
  }
  const priority: Record<string, number> = { urgent: 0, question: 1, pending: 2 }
  items.sort((a, b) => (priority[a.entry.status] ?? 3) - (priority[b.entry.status] ?? 3))
  return items
}

function TriageFeed({
  subtaskFeed,
  wsId,
  subtaskId,
  onApprove,
  onDismiss,
  onRedirect,
}: {
  subtaskFeed: FeedEntryType[]
  wsId: string
  subtaskId: string
  onApprove: (entry: FeedEntryType) => void
  onDismiss: (id: string) => void
  onRedirect: (id: string, msg: string) => void
}) {
  const actionable = subtaskFeed.filter((e) => e.status !== "done")
  const done = subtaskFeed.filter((e) => e.status === "done")
  const visible = actionable.slice(0, TRIAGE_VISIBLE)
  const hidden = actionable.length - visible.length

  return (
    <div className="space-y-2">
      {visible.map((entry) => (
        <FeedEntry
          key={entry.id}
          entry={entry}
          onApprove={() => onApprove(entry)}
          onDismiss={() => onDismiss(entry.id)}
          onRedirect={(msg) => onRedirect(entry.id, msg)}
        />
      ))}
      {hidden > 0 && (
        <div className="px-4 py-2 rounded-lg border border-dashed border-[#2a2a3e] text-center text-xs text-[#555]">
          {hidden} more in queue
        </div>
      )}
      {done.length > 0 && (
        <details className="group">
          <summary className="text-xs text-[#444] cursor-pointer select-none px-1 py-2 hover:text-[#666] list-none flex items-center gap-1">
            <span className="group-open:rotate-90 inline-block transition-transform">▸</span>
            {done.length} completed
          </summary>
          <div className="space-y-2 mt-2">
            {done.map((entry) => (
              <FeedEntry
                key={entry.id}
                entry={entry}
                onApprove={() => onApprove(entry)}
                onDismiss={() => onDismiss(entry.id)}
                onRedirect={(msg) => onRedirect(entry.id, msg)}
              />
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

function ChatFeed({
  subtaskFeed,
  wsId,
  subtaskId,
  onApprove,
  onDismiss,
  onRedirect,
}: {
  subtaskFeed: FeedEntryType[]
  wsId: string
  subtaskId: string
  onApprove: (entry: FeedEntryType) => void
  onDismiss: (id: string) => void
  onRedirect: (id: string, msg: string) => void
}) {
  // Find the most recent actionable entry — it gets action buttons
  const actionableIdx = [...subtaskFeed].map((e, i) => ({ e, i }))
    .filter(({ e }) => e.status !== "done")
    .at(-1)?.i ?? -1

  return (
    <div className="flex flex-col gap-1">
      {subtaskFeed.map((entry, idx) => (
        <FeedEntry
          key={entry.id}
          entry={entry}
          mode="chat"
          showActions={idx === actionableIdx}
          onApprove={() => onApprove(entry)}
          onDismiss={() => onDismiss(entry.id)}
          onRedirect={(msg) => onRedirect(entry.id, msg)}
        />
      ))}
      {subtaskFeed.every((e) => e.status === "running") && (
        <div className="flex items-center gap-2 px-2 py-3 text-xs text-[#555]">
          <span className="animate-pulse h-1.5 w-1.5 rounded-full bg-[#22c55e]" />
          Agent working...
        </div>
      )}
    </div>
  )
}

export function FeedPanel({ workspaces, activeWsId, activeSubtaskId, onApprove, onDismiss, onRedirect }: FeedPanelProps) {
  // Attention feed (no subtask selected)
  if (!activeSubtaskId) {
    const items = getAttentionFeed(workspaces)
    return (
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Needs Attention</h2>
          <p className="text-xs text-[#666] mt-1">
            {items.length} item{items.length !== 1 ? "s" : ""} across all workspaces
          </p>
        </div>
        {items.length === 0 ? (
          <div className="text-center text-[#555] text-sm py-16">
            All clear. Agents are working.
          </div>
        ) : (
          <div className="space-y-2">
            {items.map(({ wsId, subtaskId, entry, wsName, subtaskName }) => (
              <div key={entry.id}>
                <div className="text-[10px] text-[#555] uppercase tracking-wider mb-1 px-1">
                  {wsName} → {subtaskName}
                </div>
                <FeedEntry
                  entry={entry}
                  onApprove={() => onApprove(wsId, subtaskId, entry)}
                  onDismiss={() => onDismiss(wsId, subtaskId, entry.id)}
                  onRedirect={(msg) => onRedirect(wsId, subtaskId, entry.id, msg)}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Subtask feed
  const ws = workspaces.find((w) => w.id === activeWsId)
  const subtask = ws?.subtasks.find((s) => s.id === activeSubtaskId)

  if (!ws || !subtask) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#555] text-sm">
        Select a subtask to view its feed.
      </div>
    )
  }

  const isTriage = ws.style === "triage"

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="mb-4">
        <div className="text-[10px] text-[#555] uppercase tracking-wider mb-1">
          {ws.name} · {ws.agent}
        </div>
        <h2 className="text-lg font-semibold text-white">{subtask.name}</h2>
        <p className="text-xs text-[#888] mt-1">{subtask.detail}</p>
      </div>
      {subtask.feed.length === 0 ? (
        <div className="text-center text-[#555] text-sm py-16">
          No activity yet. Agent is working.
        </div>
      ) : isTriage ? (
        <TriageFeed
          subtaskFeed={subtask.feed}
          wsId={ws.id}
          subtaskId={subtask.id}
          onApprove={(entry) => onApprove(ws.id, subtask.id, entry)}
          onDismiss={(id) => onDismiss(ws.id, subtask.id, id)}
          onRedirect={(id, msg) => onRedirect(ws.id, subtask.id, id, msg)}
        />
      ) : (
        <ChatFeed
          subtaskFeed={subtask.feed}
          wsId={ws.id}
          subtaskId={subtask.id}
          onApprove={(entry) => onApprove(ws.id, subtask.id, entry)}
          onDismiss={(id) => onDismiss(ws.id, subtask.id, id)}
          onRedirect={(id, msg) => onRedirect(ws.id, subtask.id, id, msg)}
        />
      )}
    </div>
  )
}
