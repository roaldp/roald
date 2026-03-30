import { STATUS_CONFIG, type Status } from "../types/profile"

export function StatusBadge({ status }: { status: Status }) {
  const config = STATUS_CONFIG[status]
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ color: config.color, backgroundColor: config.bg }}
    >
      {config.label}
    </span>
  )
}
