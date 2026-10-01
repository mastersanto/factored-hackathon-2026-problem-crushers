import { useCallback, useEffect, useState } from 'react'
import { api, streamChat, type ChatEvent, type ConversationView, type Lang } from './api'
import { TEXT } from './i18n'

/** One side of an exchange. `lang` is the turn's language: the assistant's from its `done` event, and the
 *  customer's message takes the same one, since it is detected in that turn. `at` is when the browser
 *  started the turn (specs/003, data model "Turn"). */
export interface Turn {
  role: 'customer' | 'assistant'
  events: ChatEvent[]
  text?: string
  lang: Lang
  at: number
  /** Re-shown in another language (specs/004, US5): a marked translation with its original, or no translation. */
  translated?: boolean
  original?: { text: string; lang: Lang }
  translationMissing?: boolean
}

function fromView(view: ConversationView): Turn[] {
  return view.turns.map((t) => ({
    role: t.role, events: t.events ?? [], text: t.text, lang: t.lang, at: t.at,
    translated: t.translated, original: t.original, translationMissing: t.translation_missing,
  }))
}

export const STEP_ORDER = ['understand', 'decide', 'act', 'verify', 'escalate'] as const

/** Conversation state for one session. Each assistant turn keeps every streamed event, so the UI
 *  can show the verified statements, candidates, verdicts, handoffs, and the workflow trace. */
/** `lang` is the app language; `onLang` is called when a reply comes back in another one, so the whole app
 *  follows the language the customer writes in (specs/004, FR-407, FR-408). */
export function useChat(sessionId: string | null, lang: Lang, onLang: (lang: Lang) => void) {
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  const [stage, setStage] = useState('start')
  // Quick replies for the assistant's latest question; null means "use the starter examples".
  const [replies, setReplies] = useState<string[] | null>(null)
  // At least one turn has finished: the transcript has something to export.
  const [completed, setCompleted] = useState(false)
  // The language the turns are shown in, and the server session's language. When the app language differs from
  // the shown one, the conversation is re-shown (specs/004, US5): fetched as is if the server already switched
  // (a reply in another language), or after asking it to switch (the switcher).
  const [shownLang, setShownLang] = useState<Lang>(lang)
  const [serverLang, setServerLang] = useState<Lang>(lang)
  // Announced once to screen readers when a conversation is re-shown.
  const [announcement, setAnnouncement] = useState('')

  useEffect(() => {
    if (!sessionId || busy || lang === shownLang) return
    let live = true
    const load = serverLang === lang ? api.getConversation(sessionId) : api.setSessionLanguage(sessionId, lang)
    load.then((view) => {
      if (!live) return
      setTurns(fromView(view))
      setReplies(view.suggestions)
      setServerLang(view.lang)
      setShownLang(view.lang)
      if (view.turns.length) setAnnouncement(TEXT[view.lang].reshow.announced)
    }).catch(() => { if (live) setShownLang(lang) })  // keep what is shown; the next reply comes in `lang`
    return () => { live = false }
  }, [sessionId, busy, lang, shownLang, serverLang])

  const send = useCallback(async (text: string) => {
    if (!sessionId || busy || !text.trim()) return
    setBusy(true)
    const at = Date.now()
    setTurns((t) => [...t, { role: 'customer', events: [], text, lang, at }, { role: 'assistant', events: [], lang, at }])
    const push = (e: ChatEvent) => {
      if (e.type === 'done') {
        setStage(e.stage); setReplies(e.suggestions); setCompleted(true)
        if (e.lang) setServerLang(e.lang)
        if (e.lang && e.lang !== lang) onLang(e.lang)
      }
      setTurns((t) => {
        const copy = t.slice()
        const last = copy[copy.length - 1]
        copy[copy.length - 1] = { ...last, events: [...last.events, e], at: e.type === 'done' ? last.at : Date.now() }
        if (e.type === 'done' && e.lang) {
          copy[copy.length - 1].lang = e.lang
          copy[copy.length - 2] = { ...copy[copy.length - 2], lang: e.lang }
        }
        return copy
      })
    }
    try {
      await streamChat(sessionId, text, push)
    } catch (err) {
      push({ type: 'error', code: 'network', text: TEXT[lang].networkError(String(err)) })
    } finally {
      setBusy(false)
    }
  }, [sessionId, busy, lang, onLang])

  const reset = useCallback(() => { setTurns([]); setStage('start'); setReplies(null); setCompleted(false) }, [])
  return { turns, busy, stage, replies, lang, completed, send, reset, announcement }
}

/** The furthest workflow step reached in the latest assistant turn, as an index into STEP_ORDER, or null
 *  before any turn (specs/003, data model "StepProgress"). Internal steps never reach the browser. */
export function stepProgress(turns: Turn[]): number | null {
  const last = [...turns].reverse().find((t) => t.role === 'assistant')
  if (!last) return null
  let best: number | null = null
  for (const e of last.events) {
    if (e.type !== 'step') continue
    const i = STEP_ORDER.indexOf(e.step)
    if (i >= 0 && (best === null || i > best)) best = i
  }
  return best
}

// The same country-to-zone mapping as the transcript PDF (backend/app/transcript/record.py, TIME_ZONES).
const TIME_ZONES: Record<string, string> = {
  'México': 'America/Mexico_City', Mexico: 'America/Mexico_City', Colombia: 'America/Bogota',
  Argentina: 'America/Argentina/Buenos_Aires',
}

/** HH:MM in the customer's country's time zone (specs/003, R11). */
export function formatTime(at: number, country: string): string {
  return new Intl.DateTimeFormat('es', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone: TIME_ZONES[country] ?? 'America/Bogota' })
    .format(at)
}
