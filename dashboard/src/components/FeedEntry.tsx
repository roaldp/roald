import { useState } from "react"
import { StatusBadge } from "./StatusBadge"
import { FeedActions } from "./FeedActions"
import type { FeedEntry as FeedEntryType } from "../types/profile"

interface FeedEntryProps {
  entry: FeedEntryType
  onApprove: () => void
  onDismiss: () => void
  onRedirect: (message: string) => void
  mode?: "list" | "chat"
  showActions?: boolean
}

export function FeedEntry({ entry, onApprove, onDismiss, onRedirect, mode = "list", showActions = true }: FeedEntryProps) {
  const [expanded, setExpanded] = useState(false)
  const [redirecting, setRedirecting] = useState(false)
  const [redirectText, setRedirectText] = useState("")

  const isUserReply = entry.type === "user_reply"
  const isDone = entry.status === "done"

  const handleRedirectSubmit = () => {
    if (redirectText.trim()) {
      onRedirect(redirectText.trim())
      setRedirectText("")
      setRedirecting(false)
    }
  }

  // Chat bubble mode
  if (mode === "chat") {
    return (
      <div className={`flex ${isUserReply ? "justify-end" : "justify-start"} mb-3`}>
        <div
          className={`max-w-[85%] rounded-xl px-4 py-3 ${
            isUserReply
              ? "bg-[#1e3a5f] border border-[#2a4a6e] text-[#cce0ff]"
              : isDone
                ? "bg-[#0d0d17] border border-[#1a1a2e] text-[#555] opacity-70"
                : "bg-[#111120] border border-[#1e1e2e] text-[#ddd]"
          }`}
        >
          {!isUserReply && (
            <div className="flex items-center gap-2 mb-2">
              <StatusBadge status={entry.status} />
              <span className="text-[10px] text-[#555]">{entry.time}</span>
            </div>
          )}
          <div className="text-sm leading-relaxed whitespace-pre-wrap">{entry.body || entry.title}</div>
          {entry.proposedAction && showActions && !isDone && (
            <div className="mt-3 px-3 py-2 rounded bg-[#0a0a12] border border-[#2a2a3e] text-xs text-[#aaa]">
              <span className="text-[#555] mr-1">Agent will:</span>
              <span className="text-[#ccc]">{entry.proposedAction}</span>
            </div>
          )}
          {showActions && !isDone && entry.actions.length > 0 && (
            <div className="mt-3">
              <FeedActions
                actions={entry.actions}
                onApprove={onApprove}
                onDismiss={onDismiss}
                onRedirect={() => setRedirecting(!redirecting)}
              />
              {redirecting && (
                <div className="mt-2 flex gap-2">
                  <input
                    type="text"
                    value={redirectText}
                    onChange={(e) => setRedirectText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRedirectSubmit()}
                    placeholder="Add instruction or context..."
                    className="flex-1 bg-[#1a1a2e] border border-[#2a2a3e] rounded px-3 py-1.5 text-sm text-white placeholder-[#555] focus:outline-none focus:border-[#3b82f6]"
                    autoFocus
                  />
                  <button
                    onClick={handleRedirectSubmit}
                    className="px-3 py-1.5 bg-[#3b82f6] text-white rounded text-xs font-medium hover:bg-[#2563eb] transition-colors cursor-pointer"
                  >
                    Send
                  </button>
                </div>
              )}
            </div>
          )}
          {isUserReply && (
            <div className="text-[10px] text-[#4a7ab0] mt-1.5 text-right">{entry.time}</div>
          )}
        </div>
      </div>
    )
  }

  // List card mode (default)
  return (
    <div
      className={`rounded-lg border transition-colors ${
        isUserReply
          ? "border-[#3b82f6]/30 bg-[#3b82f6]/5 ml-8"
          : isDone
            ? "border-[#1e1e2e] bg-[#0d0d17]/50 opacity-60"
            : "border-[#1e1e2e] bg-[#0d0d17] hover:border-[#2a2a3e]"
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-start gap-3 cursor-pointer"
      >
        <span className="text-[#555] text-xs mt-0.5 shrink-0">{entry.time}</span>
        <span className={`flex-1 text-sm ${isDone ? "text-[#666]" : "text-[#ddd]"}`}>
          {entry.title}
        </span>
        <StatusBadge status={entry.status} />
        <span className="text-[#555] text-xs">{expanded ? "▾" : "▸"}</span>
      </button>
      {expanded && (
        <div className="px-4 pb-4 border-t border-[#1e1e2e]">
          <div className="pt-3 text-sm text-[#aaa] leading-relaxed whitespace-pre-wrap">
            {entry.body}
          </div>
          {entry.proposedAction && (
            <div className="mt-3 px-3 py-2 rounded bg-[#1a1a2e] border border-[#2a2a3e] text-xs text-[#aaa]">
              <span className="text-[#555] mr-1">Agent will:</span>
              <span className="text-[#ccc]">{entry.proposedAction}</span>
            </div>
          )}
          <FeedActions
            actions={entry.actions}
            onApprove={onApprove}
            onDismiss={onDismiss}
            onRedirect={() => setRedirecting(!redirecting)}
          />
          {redirecting && (
            <div className="mt-3 flex gap-2">
              <input
                type="text"
                value={redirectText}
                onChange={(e) => setRedirectText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRedirectSubmit()}
                placeholder="Add instruction or context..."
                className="flex-1 bg-[#1a1a2e] border border-[#2a2a3e] rounded px-3 py-1.5 text-sm text-white placeholder-[#555] focus:outline-none focus:border-[#3b82f6]"
                autoFocus
              />
              <button
                onClick={handleRedirectSubmit}
                className="px-3 py-1.5 bg-[#3b82f6] text-white rounded text-xs font-medium hover:bg-[#2563eb] transition-colors cursor-pointer"
              >
                Send
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
