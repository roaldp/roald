import { useState } from "react"

interface InputBarProps {
  placeholder: string
  onSubmit: (text: string) => void
  disabled?: boolean
  isSending?: boolean
}

export function InputBar({ placeholder, onSubmit, disabled, isSending }: InputBarProps) {
  const [value, setValue] = useState("")

  const handleSubmit = () => {
    if (value.trim() && !disabled && !isSending) {
      onSubmit(value.trim())
      setValue("")
    }
  }

  return (
    <div className="border-t border-[#1e1e2e] bg-[#0d0d17] px-4 py-3">
      <div className={`flex items-center gap-2 bg-[#1a1a2e] rounded-lg border border-[#2a2a3e] px-4 py-2 ${disabled ? "opacity-50" : ""}`}>
        <span className="text-[#555] text-sm">⌘</span>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder={isSending ? "Agent is thinking..." : disabled ? "Select a workspace to start" : placeholder}
          className="flex-1 bg-transparent text-sm text-white placeholder-[#555] focus:outline-none"
          disabled={disabled || isSending}
        />
        {value.trim() && !disabled && !isSending && (
          <button
            onClick={handleSubmit}
            className="text-xs text-[#3b82f6] hover:text-[#60a5fa] font-medium cursor-pointer"
          >
            Send
          </button>
        )}
        {isSending && (
          <span className="text-xs text-[#555] flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22c55e] animate-pulse" />
          </span>
        )}
      </div>
    </div>
  )
}
