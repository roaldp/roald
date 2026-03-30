import { useState } from "react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import type { ChatMessage as ChatMessageType, ToolCall } from "../types/profile"

interface ChatMessageProps {
  message: ChatMessageType
  onApproveTool?: (toolCall: ToolCall) => void
  onDenyTool?: (toolCall: ToolCall) => void
}

function formatTime(timestamp: string): string {
  try {
    const d = new Date(timestamp)
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  } catch {
    return ""
  }
}

// ---------------------------------------------------------------------------
// Tool classification: read-only vs action (write/send)
// ---------------------------------------------------------------------------

const ACTION_TOOLS = new Set([
  "slack_send_message",
  "slack_send_message_draft",
  "slack_schedule_message",
  "slack_create_canvas",
  "slack_update_canvas",
  "gmail_create_draft",
  "Write",
  "Edit",
  "MultiEdit",
])

function getToolActionKey(name: string): string {
  if (name.startsWith("mcp__")) {
    const parts = name.split("__")
    if (parts.length >= 3) return parts.slice(2).join("__")
  }
  return name
}

function isActionTool(name: string): boolean {
  return ACTION_TOOLS.has(getToolActionKey(name))
}

// ---------------------------------------------------------------------------
// Friendly tool names
// ---------------------------------------------------------------------------

const TOOL_MAP: Record<string, { service: string; icon: string; verb: string }> = {
  slack_send_message:       { service: "Slack",    icon: "💬", verb: "Send message" },
  slack_send_message_draft: { service: "Slack",    icon: "📝", verb: "Draft message" },
  slack_read_channel:       { service: "Slack",    icon: "👁", verb: "Read channel" },
  slack_read_thread:        { service: "Slack",    icon: "👁", verb: "Read thread" },
  slack_search_public:      { service: "Slack",    icon: "🔍", verb: "Search messages" },
  slack_search_public_and_private: { service: "Slack", icon: "🔍", verb: "Search all messages" },
  slack_search_channels:    { service: "Slack",    icon: "🔍", verb: "Search channels" },
  slack_search_users:       { service: "Slack",    icon: "🔍", verb: "Search users" },
  slack_read_user_profile:  { service: "Slack",    icon: "👤", verb: "Read profile" },
  slack_schedule_message:   { service: "Slack",    icon: "⏰", verb: "Schedule message" },
  slack_create_canvas:      { service: "Slack",    icon: "📋", verb: "Create canvas" },
  slack_read_canvas:        { service: "Slack",    icon: "👁", verb: "Read canvas" },
  slack_update_canvas:      { service: "Slack",    icon: "✏️", verb: "Update canvas" },
  gmail_search_messages:    { service: "Gmail",    icon: "🔍", verb: "Search emails" },
  gmail_read_message:       { service: "Gmail",    icon: "📧", verb: "Read email" },
  gmail_read_thread:        { service: "Gmail",    icon: "📧", verb: "Read thread" },
  gmail_create_draft:       { service: "Gmail",    icon: "📝", verb: "Draft email" },
  gmail_list_drafts:        { service: "Gmail",    icon: "📋", verb: "List drafts" },
  gmail_list_labels:        { service: "Gmail",    icon: "🏷", verb: "List labels" },
  gmail_get_profile:        { service: "Gmail",    icon: "👤", verb: "Get profile" },
  // File tools
  Read:                     { service: "Files",    icon: "📄", verb: "Read file" },
  Glob:                     { service: "Files",    icon: "🔍", verb: "Find files" },
  Grep:                     { service: "Files",    icon: "🔍", verb: "Search code" },
  Write:                    { service: "Files",    icon: "✏️", verb: "Write file" },
  Edit:                     { service: "Files",    icon: "✏️", verb: "Edit file" },
  MultiEdit:                { service: "Files",    icon: "✏️", verb: "Edit files" },
  ToolSearch:               { service: "System",   icon: "🔧", verb: "Find tools" },
}

function parseToolName(name: string): { service: string; icon: string; action: string } {
  const key = getToolActionKey(name)
  const mapped = TOOL_MAP[key]
  if (mapped) return { service: mapped.service, icon: mapped.icon, action: mapped.verb }
  const cleaned = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  return { service: "Tool", icon: "🔧", action: cleaned }
}

function describeToolAction(name: string, input: Record<string, unknown>): string {
  const key = getToolActionKey(name)

  if (key.includes("slack_send_message")) {
    const channel = input.channel_name || input.channel || ""
    const text = input.text || input.message || ""
    const preview = typeof text === "string" && text.length > 80 ? text.slice(0, 77) + "..." : text
    return `Send to ${channel}${preview ? `: "${preview}"` : ""}`
  }
  if (key.includes("gmail_create_draft")) {
    const to = input.to || ""
    const subject = input.subject || ""
    return `Draft email${to ? ` to ${to}` : ""}${subject ? `: "${subject}"` : ""}`
  }
  if (key.includes("slack_schedule")) {
    const channel = input.channel_name || input.channel || ""
    return `Schedule message to ${channel}`
  }
  return ""
}

// ---------------------------------------------------------------------------
// Collapsed tool summary for read-only tools
// ---------------------------------------------------------------------------

function ToolSummary({ tools, expanded, onToggle }: {
  tools: ToolCall[]
  expanded: boolean
  onToggle: () => void
}) {
  // Group by service
  const groups: Record<string, number> = {}
  for (const tc of tools) {
    const { service } = parseToolName(tc.name)
    groups[service] = (groups[service] || 0) + 1
  }
  const summary = Object.entries(groups)
    .map(([service, count]) => `${service} (${count})`)
    .join(", ")

  const allDone = tools.every((tc) => tc.status === "executed")
  const anyRunning = tools.some((tc) => tc.status === "approved")

  return (
    <div className="mt-2">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 text-[11px] text-[#666] hover:text-[#888] transition-colors cursor-pointer"
      >
        {anyRunning ? (
          <span className="h-1.5 w-1.5 rounded-full bg-[#3b82f6] animate-pulse" />
        ) : allDone ? (
          <span className="text-[#22c55e]">✓</span>
        ) : (
          <span>◦</span>
        )}
        <span>
          {anyRunning ? "Running" : "Used"} {tools.length} tool{tools.length !== 1 ? "s" : ""}: {summary}
        </span>
        <span className="text-[10px]">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="mt-1.5 ml-3 border-l border-[#1e1e2e] pl-3 space-y-1">
          {tools.map((tc) => {
            const parsed = parseToolName(tc.name)
            const isDone = tc.status === "executed"
            const isRunning = tc.status === "approved"
            return (
              <div key={tc.id} className="flex items-center gap-2 text-[11px] text-[#555]">
                {isRunning ? (
                  <span className="h-1 w-1 rounded-full bg-[#3b82f6] animate-pulse" />
                ) : isDone ? (
                  <span className="text-[#22c55e] text-[9px]">✓</span>
                ) : (
                  <span className="text-[9px]">◦</span>
                )}
                <span>{parsed.icon}</span>
                <span>{parsed.action}</span>
                {tc.result && (
                  <span className="text-[#444] truncate max-w-[200px]">
                    — {tc.result.slice(0, 60)}{tc.result.length > 60 ? "..." : ""}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Action tool card (only for write/send operations that need approval)
// ---------------------------------------------------------------------------

function ActionToolCard({
  toolCall,
  onApprove,
  onDeny,
}: {
  toolCall: ToolCall
  onApprove?: () => void
  onDeny?: () => void
}) {
  const showActions = toolCall.status === "needs_approval" || toolCall.status === "proposed"
  const isExecuting = toolCall.status === "approved"
  const isDone = toolCall.status === "executed"
  const isDenied = toolCall.status === "denied"
  const isError = toolCall.status === "error"
  const parsed = parseToolName(toolCall.name)
  const description = describeToolAction(toolCall.name, toolCall.input)

  const borderColor = isDone ? "border-[#22c55e]/20" :
    isDenied ? "border-[#666]/20" :
    isError ? "border-[#ef4444]/20" :
    isExecuting ? "border-[#3b82f6]/20" :
    "border-[#eab308]/25"

  const bgColor = isDone ? "bg-[#22c55e]/5" :
    isDenied ? "bg-[#666]/5" :
    isError ? "bg-[#ef4444]/5" :
    isExecuting ? "bg-[#3b82f6]/5" :
    "bg-[#eab308]/5"

  return (
    <div className={`mt-3 rounded-lg border ${borderColor} ${bgColor} p-3`}>
      <div className="flex items-center gap-2">
        <span className="text-sm">{parsed.icon}</span>
        <span className="text-xs font-medium text-[#aaa]">{parsed.service}</span>
        <span className="text-[10px] text-[#555]">·</span>
        <span className="text-xs text-[#777]">{parsed.action}</span>
        {isDone && <span className="text-[10px] text-[#22c55e] ml-auto">Done</span>}
        {isDenied && <span className="text-[10px] text-[#666] ml-auto">Skipped</span>}
        {isError && <span className="text-[10px] text-[#ef4444] ml-auto">Failed</span>}
        {isExecuting && (
          <span className="text-[10px] text-[#3b82f6] ml-auto flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3b82f6] animate-pulse" />
            running...
          </span>
        )}
      </div>

      {description && (
        <div className="text-sm text-[#ccc] mt-1.5">
          {description}
        </div>
      )}

      {toolCall.result && (
        <div className="text-xs text-[#999] mt-1.5 border-t border-[#333]/30 pt-2">
          {toolCall.result.length > 200 ? toolCall.result.slice(0, 197) + "..." : toolCall.result}
        </div>
      )}

      {showActions && (
        <div className="flex gap-2 mt-2.5">
          <button
            onClick={onApprove}
            className="px-4 py-1.5 text-xs font-medium rounded-md bg-[#22c55e]/15 text-[#22c55e] border border-[#22c55e]/30 hover:bg-[#22c55e]/25 transition-colors cursor-pointer"
          >
            Allow
          </button>
          <button
            onClick={onDeny}
            className="px-4 py-1.5 text-xs font-medium rounded-md bg-[#666]/10 text-[#777] border border-[#666]/20 hover:bg-[#666]/20 transition-colors cursor-pointer"
          >
            Deny
          </button>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Markdown renderer with dark theme styling
// ---------------------------------------------------------------------------

function MarkdownContent({ content, className }: { content: string; className?: string }) {
  return (
    <div className={`prose-dark ${className || ""}`}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => <h1 className="text-base font-bold text-white mt-3 mb-1">{children}</h1>,
          h2: ({ children }) => <h2 className="text-sm font-bold text-white mt-3 mb-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold text-[#ddd] mt-2 mb-1">{children}</h3>,
          // Paragraphs
          p: ({ children }) => <p className="text-sm leading-relaxed text-[#ccc] mb-2 last:mb-0">{children}</p>,
          // Bold / italic
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="text-[#bbb]">{children}</em>,
          // Lists
          ul: ({ children }) => <ul className="text-sm text-[#ccc] list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
          ol: ({ children }) => <ol className="text-sm text-[#ccc] list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
          li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
          // Tables (GFM)
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="text-xs border-collapse w-full">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="border-b border-[#333]">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border-b border-[#1e1e2e]">{children}</tr>,
          th: ({ children }) => (
            <th className="text-left text-[#999] font-medium px-2 py-1.5 text-[11px] uppercase tracking-wide">
              {children}
            </th>
          ),
          td: ({ children }) => <td className="text-[#ccc] px-2 py-1.5">{children}</td>,
          // Code
          code: ({ children, className: codeClass }) => {
            const isBlock = codeClass?.startsWith("language-")
            if (isBlock) {
              return (
                <pre className="bg-[#0a0a14] rounded-md p-3 my-2 overflow-x-auto">
                  <code className="text-[11px] text-[#aaa] font-mono">{children}</code>
                </pre>
              )
            }
            return <code className="text-[12px] bg-[#1a1a2a] px-1 py-0.5 rounded text-[#ddd] font-mono">{children}</code>
          },
          pre: ({ children }) => <>{children}</>,
          // Links
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#60a5fa] hover:underline">
              {children}
            </a>
          ),
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-[#333] pl-3 my-2 text-[#999]">{children}</blockquote>
          ),
          // Horizontal rules
          hr: () => <hr className="border-[#1e1e2e] my-3" />,
        }}
      >
        {content}
      </Markdown>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main ChatMessage component
// ---------------------------------------------------------------------------

export function ChatMessage({ message, onApproveTool, onDenyTool }: ChatMessageProps) {
  const isUser = message.role === "user"
  const [toolsExpanded, setToolsExpanded] = useState(false)

  // Separate tool calls:
  // - Needs attention (approval or error): full card with buttons or error display
  // - Completed read-only: collapsed summary
  // - Completed actions: full card showing result
  const needsAttention = (tc: ToolCall) =>
    tc.status === "proposed" || tc.status === "needs_approval" || tc.status === "error"
  const attentionTools = message.toolCalls?.filter((tc) => needsAttention(tc)) || []
  const completedReadOnly = message.toolCalls?.filter((tc) => !needsAttention(tc) && !isActionTool(tc.name)) || []
  const completedActions = message.toolCalls?.filter((tc) => !needsAttention(tc) && isActionTool(tc.name)) || []

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 ${
          isUser
            ? "bg-[#1e3a5f] border border-[#2a4a6e]"
            : "bg-[#111120] border border-[#1e1e2e]"
        }`}
      >
        {/* Message content with markdown */}
        {message.content && (
          isUser ? (
            <div className="text-sm leading-relaxed whitespace-pre-wrap text-[#cce0ff]">
              {message.content}
            </div>
          ) : (
            <MarkdownContent content={message.content} />
          )
        )}

        {/* Tools needing attention: approval prompts or errors */}
        {attentionTools.map((tc) => (
          <ActionToolCard
            key={tc.id}
            toolCall={tc}
            onApprove={() => onApproveTool?.(tc)}
            onDeny={() => onDenyTool?.(tc)}
          />
        ))}

        {/* Completed read-only tools: collapsed summary */}
        {completedReadOnly.length > 0 && (
          <ToolSummary
            tools={completedReadOnly}
            expanded={toolsExpanded}
            onToggle={() => setToolsExpanded(!toolsExpanded)}
          />
        )}

        {/* Completed action tools: full cards (no buttons, already resolved) */}
        {completedActions.map((tc) => (
          <ActionToolCard
            key={tc.id}
            toolCall={tc}
          />
        ))}

        <div
          className={`text-[10px] mt-2 ${
            isUser ? "text-[#4a7ab0] text-right" : "text-[#444]"
          }`}
        >
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  )
}
