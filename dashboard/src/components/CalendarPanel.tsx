import type { AgendaItem, SourceStatus } from "../types/profile"

interface CalendarPanelProps {
  agenda: AgendaItem[]
  sourceStatus?: SourceStatus[]
  onEventClick: (item: AgendaItem) => void
}

const statusStyles = {
  done: "text-[#555] line-through",
  next: "text-white font-medium",
  upcoming: "text-[#999]",
}

const dotStyles = {
  done: "bg-[#555]",
  next: "bg-[#22c55e]",
  upcoming: "bg-[#333]",
}

const sourceStatusColors = {
  active: "#22c55e",
  error: "#ef4444",
  pending_discovery: "#f97316",
}

export function CalendarPanel({ agenda, sourceStatus, onEventClick }: CalendarPanelProps) {
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  })

  return (
    <div className="w-56 shrink-0 border-l border-[#1e1e2e] bg-[#0a0a14] flex flex-col overflow-hidden">
      <div className="px-4 pt-4 pb-2">
        <h3 className="text-xs text-[#666] uppercase tracking-wider font-medium">Today</h3>
        <p className="text-[10px] text-[#444] mt-0.5">{today}</p>
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {agenda.map((item, i) => (
          <button
            key={i}
            onClick={() => onEventClick(item)}
            className="w-full text-left px-3 py-2.5 rounded hover:bg-[#161625] transition-colors flex items-start gap-2.5 cursor-pointer"
          >
            <span className={`inline-block h-2 w-2 rounded-full mt-1 shrink-0 ${dotStyles[item.status]}`} />
            <div className="flex-1 min-w-0">
              <div className="text-[10px] text-[#555]">{item.time}</div>
              <div className={`text-xs truncate ${statusStyles[item.status]}`}>
                {item.event}
              </div>
            </div>
          </button>
        ))}
      </div>
      {sourceStatus && sourceStatus.length > 0 && (
        <div className="border-t border-[#1e1e2e] px-4 py-3">
          <h3 className="text-[10px] text-[#444] uppercase tracking-wider font-medium mb-2">Sources</h3>
          <div className="space-y-1.5">
            {sourceStatus.map((s) => (
              <div key={s.name} className="flex items-center gap-2">
                <span
                  className="h-1.5 w-1.5 rounded-full shrink-0"
                  style={{ backgroundColor: sourceStatusColors[s.status] }}
                />
                <span className="text-[11px] text-[#777] truncate">{s.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
