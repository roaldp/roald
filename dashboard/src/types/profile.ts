export type Status = "pending" | "question" | "running" | "done" | "urgent"
export type TrafficLight = "green" | "yellow" | "red"

export interface Identity {
  companionName: string
  orgName: string
  modelName: string
}

export interface ActionDef {
  type: "approve" | "dismiss" | "redirect"
  label: string
}

export interface FeedEntry {
  id: string
  type: "agent_output" | "user_reply" | "handoff_suggestion" | "escalation"
  status: Status
  title: string
  body: string
  time: string
  actions: ActionDef[]
  downstreamEffect?: string
  proposedAction?: string
}

export interface Subtask {
  id: string
  name: string
  detail: string
  status: Status
  light: TrafficLight
  feed: FeedEntry[]
}

export interface Workspace {
  id: string
  icon: string
  name: string
  agent: string
  style?: "triage" | "chat"
  subtasks: Subtask[]
}

export interface SourceStatus {
  name: string
  status: "active" | "error" | "pending_discovery"
  notes?: string
}

export interface AgendaItem {
  time: string
  event: string
  status: "done" | "next" | "upcoming"
  relatedWsIds?: string[]
}

export interface Profile {
  identity: Identity
  workspaces: Workspace[]
  agenda: AgendaItem[]
  inputPlaceholder: string
  sourceStatus?: SourceStatus[]
}

// Status configuration: colors and labels
export const STATUS_CONFIG: Record<Status, { color: string; bg: string; label: string }> = {
  urgent:   { color: "#ef4444", bg: "rgba(239,68,68,0.15)",  label: "Urgent" },
  question: { color: "#eab308", bg: "rgba(234,179,8,0.15)",  label: "Question" },
  pending:  { color: "#3b82f6", bg: "rgba(59,130,246,0.15)", label: "Pending" },
  running:  { color: "#22c55e", bg: "rgba(34,197,94,0.15)",  label: "Running" },
  done:     { color: "#6b7280", bg: "rgba(107,114,128,0.15)", label: "Done" },
}

export const TRAFFIC_COLORS: Record<TrafficLight, string> = {
  green:  "#22c55e",
  yellow: "#eab308",
  red:    "#ef4444",
}

// Conversation types
export interface ToolCall {
  id: string
  name: string
  input: Record<string, unknown>
  status: "proposed" | "needs_approval" | "approved" | "denied" | "executed" | "error"
  result?: string
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  toolCalls?: ToolCall[]
}

export interface Thread {
  threadId: string
  label: string
  messageCount: number
}
