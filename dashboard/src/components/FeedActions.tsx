import type { ActionDef } from "../types/profile"

interface FeedActionsProps {
  actions: ActionDef[]
  onApprove: () => void
  onDismiss: () => void
  onRedirect: () => void
}

export function FeedActions({ actions, onApprove, onDismiss, onRedirect }: FeedActionsProps) {
  if (actions.length === 0) return null

  const handlers: Record<string, () => void> = {
    approve: onApprove,
    dismiss: onDismiss,
    redirect: onRedirect,
  }

  const styles: Record<string, string> = {
    approve: "bg-[#22c55e]/20 text-[#22c55e] hover:bg-[#22c55e]/30",
    dismiss: "bg-[#ef4444]/10 text-[#ef4444]/70 hover:bg-[#ef4444]/20",
    redirect: "bg-[#3b82f6]/10 text-[#3b82f6] hover:bg-[#3b82f6]/20",
  }

  return (
    <div className="flex items-center gap-2 mt-3">
      {actions.map((action) => (
        <button
          key={action.type}
          onClick={handlers[action.type]}
          className={`px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${styles[action.type] || ""}`}
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
