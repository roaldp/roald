import { TRAFFIC_COLORS, type TrafficLight } from "../types/profile"

export function SubtaskDot({ light }: { light: TrafficLight }) {
  return (
    <span
      className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
      style={{ backgroundColor: TRAFFIC_COLORS[light] }}
    />
  )
}
