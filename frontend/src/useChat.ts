import { useCallback, useState } from 'react'
import { streamChat, type ChatEvent } from './api'

export interface Turn { role: 'customer' | 'assistant'; events: ChatEvent[]; text?: string }

/** Conversation state for one session. Each assistant turn keeps every streamed event, so the UI
 *  can show the verified statements, candidates, verdicts, handoffs, and the workflow trace. */
export function useChat(sessionId: string | null) {
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  const [stage, setStage] = useState('start')
  // Quick replies for the assistant's latest question; null means "use the starter examples".
  const [replies, setReplies] = useState<string[] | null>(null)

  const send = useCallback(async (text: string) => {
    if (!sessionId || busy || !text.trim()) return
    setBusy(true)
    setTurns((t) => [...t, { role: 'customer', events: [], text }, { role: 'assistant', events: [] }])
    const push = (e: ChatEvent) => {
      if (e.type === 'done') { setStage(e.stage); setReplies(e.suggestions) }
      setTurns((t) => {
        const copy = t.slice()
        const last = copy[copy.length - 1]
        copy[copy.length - 1] = { ...last, events: [...last.events, e] }
        return copy
      })
    }
    try {
      await streamChat(sessionId, text, push)
    } catch (err) {
      push({ type: 'error', code: 'network', text: `No se pudo contactar el servicio (${String(err)}).` })
    } finally {
      setBusy(false)
    }
  }, [sessionId, busy])

  const reset = useCallback(() => { setTurns([]); setStage('start'); setReplies(null) }, [])
  return { turns, busy, stage, replies, send, reset }
}
