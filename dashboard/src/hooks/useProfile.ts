import { useState, useEffect, useRef } from "react"
import type { Profile } from "../types/profile"

const POLL_INTERVAL = 30_000

export function useProfile() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const lastJson = useRef<string>("")

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>

    async function load() {
      try {
        const res = await fetch(`/profile.json?t=${Date.now()}`)
        if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`)
        const text = await res.text()
        if (text !== lastJson.current) {
          lastJson.current = text
          setProfile(JSON.parse(text))
        }
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error")
      } finally {
        setIsLoading(false)
      }
    }

    load()
    timer = setInterval(load, POLL_INTERVAL)
    return () => clearInterval(timer)
  }, [])

  return { profile, isLoading, error }
}
