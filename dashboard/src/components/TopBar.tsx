import { useState } from "react"
import type { Identity, SourceStatus } from "../types/profile"

interface TopBarProps {
  identity: Identity
  sourceStatus?: SourceStatus[]
}

function SourceStatusDot({ sources }: { sources: SourceStatus[] }) {
  const [hovered, setHovered] = useState(false)

  const hasError = sources.some((s) => s.status === "error")
  const hasPending = sources.some((s) => s.status === "pending_discovery")
  const dotColor = sources.length === 0 ? "#444" : hasError ? "#ef4444" : hasPending ? "#f97316" : "#22c55e"

  const statusLabel: Record<SourceStatus["status"], string> = {
    active: "active",
    error: "error",
    pending_discovery: "pending",
  }

  return (
    <div
      className="relative flex items-center gap-2 cursor-pointer"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span
        className="h-2.5 w-2.5 rounded-full inline-block"
        style={{ backgroundColor: dotColor, boxShadow: `0 0 6px ${dotColor}66` }}
      />
      <span className="text-xs text-[#666]">Sources</span>
      {hovered && sources.length > 0 && (
        <div className="absolute right-0 top-6 z-50 bg-[#111120] border border-[#2a2a3e] rounded-lg p-3 min-w-[220px] shadow-xl">
          <div className="text-[10px] text-[#555] uppercase tracking-wider mb-2">Connected sources</div>
          <div className="space-y-1.5">
            {sources.map((s) => (
              <div key={s.name} className="flex items-start gap-2">
                <span
                  className="h-1.5 w-1.5 rounded-full mt-1.5 shrink-0"
                  style={{
                    backgroundColor:
                      s.status === "active" ? "#22c55e" : s.status === "error" ? "#ef4444" : "#f97316",
                  }}
                />
                <div>
                  <span className="text-xs text-[#ccc]">{s.name}</span>
                  <span className="text-[10px] text-[#555] ml-1.5">{statusLabel[s.status]}</span>
                  {s.notes && <div className="text-[10px] text-[#555] mt-0.5">{s.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {hovered && sources.length === 0 && (
        <div className="absolute right-0 top-6 z-50 bg-[#111120] border border-[#2a2a3e] rounded-lg p-3 shadow-xl">
          <div className="text-xs text-[#555]">No sources connected yet</div>
        </div>
      )}
    </div>
  )
}

export function TopBar({ identity, sourceStatus }: TopBarProps) {
  return (
    <div className="flex items-center justify-between px-5 py-3 border-b border-[#1e1e2e] bg-[#0d0d17]">
      <div className="flex items-center gap-3">
        <div className="flex gap-1.5">
          <span className="h-3 w-3 rounded-full bg-[#ef4444]" />
          <span className="h-3 w-3 rounded-full bg-[#eab308]" />
          <span className="h-3 w-3 rounded-full bg-[#22c55e]" />
        </div>
        <span className="text-sm font-semibold text-white">
          {identity.companionName}
        </span>
        <span className="text-xs text-[#666]">
          {identity.orgName} · {identity.modelName}
        </span>
      </div>
      <SourceStatusDot sources={sourceStatus ?? []} />
    </div>
  )
}
