import { useState, useEffect, useCallback, useRef } from "react"
import type { ChatMessage, Thread, ToolCall } from "../types/profile"

interface UseConversationReturn {
  messages: ChatMessage[]
  threads: Thread[]
  activeThreadId: string
  isLoading: boolean
  isSending: boolean
  sendMessage: (text: string) => Promise<void>
  switchThread: (threadId: string) => void
  initWorkspace: () => Promise<void>
  createThread: (label: string) => void
  approveTool: (msg: ChatMessage, toolCall: ToolCall) => Promise<void>
  denyTool: (msg: ChatMessage, toolCall: ToolCall) => void
}

export function useConversation(activeWsId: string | null): UseConversationReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState("main")
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const prevWsId = useRef<string | null>(null)

  const loadConversation = useCallback(async (wsId: string, threadId: string) => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/conversations/${wsId}/${threadId}`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages || [])
      } else {
        setMessages([])
      }
    } catch {
      setMessages([])
    }
    setIsLoading(false)
  }, [])

  const loadThreads = useCallback(async (wsId: string) => {
    try {
      const res = await fetch(`/api/conversations/${wsId}`)
      if (res.ok) {
        const data = await res.json()
        setThreads(data.threads || [])
      }
    } catch {
      setThreads([{ threadId: "main", label: "Main", messageCount: 0 }])
    }
  }, [])

  // When workspace changes, load threads + main conversation
  useEffect(() => {
    if (!activeWsId) {
      setMessages([])
      setThreads([])
      setActiveThreadId("main")
      return
    }

    if (activeWsId !== prevWsId.current) {
      prevWsId.current = activeWsId
      setActiveThreadId("main")
      loadThreads(activeWsId)
      loadConversation(activeWsId, "main")
    }
  }, [activeWsId, loadThreads, loadConversation])

  const initWorkspace = useCallback(async () => {
    if (!activeWsId) return
    setIsSending(true)
    try {
      const res = await fetch(`/api/conversations/${activeWsId}/${activeThreadId}/init`, {
        method: "POST",
      })
      if (res.ok) {
        const data = await res.json()
        if (data.message) {
          setMessages((prev) => [...prev, data.message])
        }
      }
    } catch {
      // Silently fail — workspace just shows empty
    }
    setIsSending(false)
  }, [activeWsId, activeThreadId])

  // Auto-init when conversation is empty after loading
  const hasAutoInited = useRef<Set<string>>(new Set())
  useEffect(() => {
    if (!activeWsId || isLoading || isSending) return
    const key = `${activeWsId}:${activeThreadId}`
    if (messages.length === 0 && !hasAutoInited.current.has(key)) {
      hasAutoInited.current.add(key)
      initWorkspace()
    }
  }, [activeWsId, activeThreadId, messages.length, isLoading, isSending, initWorkspace])

  const sendMessage = useCallback(async (text: string) => {
    if (!activeWsId || !text.trim() || isSending) return

    // Optimistically add user message
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text.trim(),
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsSending(true)

    // Create placeholder assistant message for streaming
    const assistantMsgId = `msg-${Date.now()}-assistant`
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      toolCalls: [],
    }
    setMessages((prev) => [...prev, assistantMsg])

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspaceId: activeWsId,
          threadId: activeThreadId,
          message: text.trim(),
        }),
      })

      if (!res.ok || !res.body) {
        // Fallback: try non-streaming endpoint
        const fallbackRes = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            workspaceId: activeWsId,
            threadId: activeThreadId,
            message: text.trim(),
          }),
        })
        if (fallbackRes.ok) {
          const data = await fallbackRes.json()
          if (data.message) {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantMsgId ? data.message : m))
            )
          }
        }
        setIsSending(false)
        return
      }

      // Parse SSE stream
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let accumulatedText = ""
      const accumulatedToolCalls: ToolCall[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE events from buffer
        const lines = buffer.split("\n")
        buffer = lines.pop() || "" // Keep incomplete line in buffer

        let eventType = ""
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith("data: ") && eventType) {
            try {
              const data = JSON.parse(line.slice(6))
              if (eventType === "text_delta") {
                accumulatedText += data.content || ""
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: accumulatedText }
                      : m
                  )
                )
              } else if (eventType === "tool_use") {
                accumulatedToolCalls.push(data as ToolCall)
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, toolCalls: [...accumulatedToolCalls] }
                      : m
                  )
                )
              } else if (eventType === "tool_result") {
                // Update the matching tool call with result
                const idx = accumulatedToolCalls.findIndex(
                  (tc) => tc.id === data.tool_use_id
                )
                if (idx >= 0) {
                  accumulatedToolCalls[idx] = {
                    ...accumulatedToolCalls[idx],
                    status: "executed",
                    result: data.content,
                  }
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMsgId
                        ? { ...m, toolCalls: [...accumulatedToolCalls] }
                        : m
                    )
                  )
                }
              } else if (eventType === "done") {
                // Final update with complete text
                const finalText = data.text || accumulatedText
                const finalTools = data.toolCalls || accumulatedToolCalls
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          content: finalText,
                          toolCalls: finalTools.length > 0 ? finalTools : undefined,
                        }
                      : m
                  )
                )
              } else if (eventType === "error") {
                accumulatedText += `\n\nError: ${data.message || "Unknown error"}`
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: accumulatedText }
                      : m
                  )
                )
              }
            } catch {
              // Skip malformed JSON
            }
            eventType = ""
          }
        }
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: "Failed to get a response. Is the server running?" }
            : m
        )
      )
    }
    setIsSending(false)
  }, [activeWsId, activeThreadId, isSending])

  const approveTool = useCallback(async (msg: ChatMessage, toolCall: ToolCall) => {
    if (!activeWsId) return

    // Optimistically update tool call status
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== msg.id) return m
        return {
          ...m,
          toolCalls: m.toolCalls?.map((tc) =>
            tc.id === toolCall.id ? { ...tc, status: "approved" as const } : tc
          ),
        }
      })
    )

    try {
      const res = await fetch("/api/chat/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspaceId: activeWsId,
          threadId: activeThreadId,
          toolName: toolCall.name,
          toolInput: toolCall.input,
          approved: true,
        }),
      })

      if (res.ok) {
        const data = await res.json()
        if (data.message) {
          // Update the tool call status and add result message
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msg.id) return m
              return {
                ...m,
                toolCalls: m.toolCalls?.map((tc) =>
                  tc.id === toolCall.id
                    ? { ...tc, status: "executed" as const, result: data.message.content }
                    : tc
                ),
              }
            })
          )
          // Add the execution result as a new message
          if (data.message.content) {
            setMessages((prev) => [...prev, data.message])
          }
        }
      }
    } catch {
      // Revert on error
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== msg.id) return m
          return {
            ...m,
            toolCalls: m.toolCalls?.map((tc) =>
              tc.id === toolCall.id
                ? { ...tc, status: "error" as const, result: "Failed to execute" }
                : tc
            ),
          }
        })
      )
    }
  }, [activeWsId, activeThreadId])

  const denyTool = useCallback((msg: ChatMessage, toolCall: ToolCall) => {
    setMessages((prev) =>
      prev.map((m) => {
        if (m.id !== msg.id) return m
        return {
          ...m,
          toolCalls: m.toolCalls?.map((tc) =>
            tc.id === toolCall.id ? { ...tc, status: "denied" as const } : tc
          ),
        }
      })
    )

    // Fire and forget — persist denial on server
    if (activeWsId) {
      fetch("/api/chat/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspaceId: activeWsId,
          threadId: activeThreadId,
          toolName: toolCall.name,
          toolInput: toolCall.input,
          approved: false,
        }),
      }).catch(() => {})
    }
  }, [activeWsId, activeThreadId])

  const switchThread = useCallback((threadId: string) => {
    if (!activeWsId || threadId === activeThreadId) return
    setActiveThreadId(threadId)
    loadConversation(activeWsId, threadId)
  }, [activeWsId, activeThreadId, loadConversation])

  const createThread = useCallback((label: string) => {
    const slug = label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")
    const threadId = `thread-${slug}`
    setThreads((prev) => [...prev, { threadId, label, messageCount: 0 }])
    setActiveThreadId(threadId)
    setMessages([])
  }, [])

  return {
    messages,
    threads,
    activeThreadId,
    isLoading,
    isSending,
    sendMessage,
    switchThread,
    initWorkspace,
    createThread,
    approveTool,
    denyTool,
  }
}
