import { useState, useCallback, useEffect } from "react"
import type { Profile, FeedEntry, Workspace } from "../types/profile"

interface Toast {
  message: string
  visible: boolean
}

export function useFeedState(profile: Profile | null) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [toast, setToast] = useState<Toast>({ message: "", visible: false })

  // Initialize from profile
  useEffect(() => {
    if (profile) {
      setWorkspaces(profile.workspaces)
    }
  }, [profile])

  const showToast = useCallback((message: string) => {
    setToast({ message, visible: true })
    setTimeout(() => setToast({ message: "", visible: false }), 3000)
  }, [])

  const updateFeedEntry = useCallback(
    (wsId: string, subtaskId: string, entryId: string, updater: (entry: FeedEntry) => FeedEntry | null) => {
      setWorkspaces((prev) =>
        prev.map((ws) => {
          if (ws.id !== wsId) return ws
          return {
            ...ws,
            subtasks: ws.subtasks.map((st) => {
              if (st.id !== subtaskId) return st
              return {
                ...st,
                feed: st.feed
                  .map((fe) => (fe.id === entryId ? updater(fe) : fe))
                  .filter((fe): fe is FeedEntry => fe !== null),
              }
            }),
          }
        })
      )
    },
    []
  )

  const approve = useCallback(
    (wsId: string, subtaskId: string, entry: FeedEntry) => {
      updateFeedEntry(wsId, subtaskId, entry.id, (fe) => ({
        ...fe,
        status: "done",
        actions: [],
      }))
      if (entry.downstreamEffect) {
        showToast(entry.downstreamEffect)
      } else {
        showToast("Approved")
      }
    },
    [updateFeedEntry, showToast]
  )

  const dismiss = useCallback(
    (wsId: string, subtaskId: string, entryId: string) => {
      updateFeedEntry(wsId, subtaskId, entryId, () => null)
      showToast("Dismissed")
    },
    [updateFeedEntry, showToast]
  )

  const redirect = useCallback(
    (wsId: string, subtaskId: string, entryId: string, message: string) => {
      setWorkspaces((prev) =>
        prev.map((ws) => {
          if (ws.id !== wsId) return ws
          return {
            ...ws,
            subtasks: ws.subtasks.map((st) => {
              if (st.id !== subtaskId) return st
              const entryIndex = st.feed.findIndex((fe) => fe.id === entryId)
              if (entryIndex === -1) return st
              const newReply: FeedEntry = {
                id: `reply-${Date.now()}`,
                type: "user_reply",
                status: "running",
                title: message,
                body: message,
                time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                actions: [],
              }
              const newFeed = [...st.feed]
              newFeed.splice(entryIndex + 1, 0, newReply)
              return { ...st, feed: newFeed }
            }),
          }
        })
      )
      showToast("Instruction sent")
    },
    [showToast]
  )

  return { workspaces, toast, approve, dismiss, redirect }
}
