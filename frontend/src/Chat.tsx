import { useEffect, useRef, useState, type ReactNode } from 'react'
import { downloadTranscript, HttpError, type ChatEvent } from './api'
import { CandidateList } from './components/CandidateList'
import { CaseCard } from './components/CaseCard'
import { Statements } from './components/Statements'
import { StepsPanel } from './components/StepsPanel'
import { VerdictCard } from './components/VerdictCard'
import { TEXT } from './i18n'
import { Icon } from './icons'
import { useLanguage } from './language'
import { formatTime, stepProgress, useChat, type Turn } from './useChat'

interface Props {
  sessionId: string
  conversationRef: string
  firstName: string
  country: string
  suggestions: string[]
  onChangeCustomer: () => void
}

/** The customer's chat (specs/003 design, "Screen Chat"). Every fixed text follows the language of the latest
 *  assistant message (FR-201); what the assistant says is shown exactly as the server streamed it. */
export function Chat({ sessionId, conversationRef, firstName, country, suggestions, onChangeCustomer }: Props) {
  // Every fixed text follows the app language, which follows the language the customer writes in (specs/004).
  const { lang, setLang } = useLanguage()
  const { turns, busy, replies, completed, send } = useChat(sessionId, lang, setLang)
  const t = TEXT[lang]
  const [pdf, setPdf] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null)
  const [pdfExpired, setPdfExpired] = useState(false)
  const [text, setText] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const end = useRef<HTMLDivElement>(null)
  const typed = useRef(false)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    end.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'end' })
  }, [turns])
  // After a typed message, focus returns to the text box once the reply is in (FR-212).
  useEffect(() => { if (!busy && typed.current) { typed.current = false; input.current?.focus() } }, [busy])

  const lastAssistant = [...turns].reverse().find((x) => x.role === 'assistant')
  const ended = pdfExpired || !!lastAssistant?.events.some((e) => e.type === 'error' && (e.code === 'session_expired' || e.code === 'turn_limit'))
  const endedText = lastAssistant?.events.find((e): e is Extract<ChatEvent, { type: 'error' }> =>
    e.type === 'error' && (e.code === 'session_expired' || e.code === 'turn_limit'))?.text ?? t.session.expiredBody

  const download = async () => {
    try {
      const code = await downloadTranscript(sessionId, conversationRef)
      setPdf({ tone: 'good', text: `${t.pdf.saved}: ${code}` })
    } catch (err) {
      if (err instanceof HttpError && err.status === 401) { setPdfExpired(true); setPdf({ tone: 'bad', text: t.pdf.expired }) }
      else setPdf({ tone: 'bad', text: `${t.pdf.failed} (${String(err)})` })
    }
  }
  const submit = (value: string, fromComposer = false) => {
    if (!value.trim() || busy) return
    typed.current = fromComposer
    void send(value)
    setText('')
  }

  return (
    <>
      <section className="panel customer-bar" aria-label={t.aria.customer}>
        <div className="cb-who">
          <span className="avatar navy" aria-hidden="true">{firstName.slice(0, 1).toUpperCase()}</span>
          <div className="cb-name"><strong>{firstName}</strong><span className="muted small">{country}</span></div>
          <button type="button" className="link-btn" onClick={onChangeCustomer}>{t.session.change}</button>
        </div>
        <div className="cb-pdf">
          <button type="button" className="btn" disabled={busy || !completed || ended} onClick={() => void download()}
            aria-describedby={!completed ? 'pdf-not-yet' : undefined}>
            <Icon name="download" />{t.pdf.button}
          </button>
          {!completed && <span id="pdf-not-yet" className="muted small">{t.pdf.notYet}</span>}
          <span role="status" className={pdf?.tone}>{pdf && <><Icon name={pdf.tone === 'good' ? 'task_alt' : 'block'} size={18} />{pdf.text}</>}</span>
        </div>
      </section>

      <StepsPanel variant="drawer" progress={stepProgress(turns)} trace={lastAssistant?.events ?? []} lang={lang} />

      <div className="chat-grid">
        <section className="panel conversation" aria-label={t.aria.messages}>
          <div className="log" role="log" aria-live="polite" aria-label={t.aria.messages}>
            <div className="intro"><p>{t.intro(firstName)}</p><p>{t.languages}</p></div>
            {turns.map((turn, i) => (
              <TurnView key={i} turn={turn} next={turns[i + 1]} country={country} busy={busy} onPick={(v) => submit(v)} />
            ))}
            {busy && (
              <div className="typing">
                <span className="avatar navy" aria-hidden="true"><Icon name="account_balance" size={18} /></span>
                <div className="typing-bubble"><span className="dots" aria-hidden="true"><span /><span /><span /></span>{t.typing}</div>
              </div>
            )}
            <div ref={end} />
          </div>

          {!ended && (replies
            ? <div className="chips replies" role="group" aria-label={t.aria.replies}>
                {replies.map((s) => <button type="button" key={s} className="chip" disabled={busy} onClick={() => submit(s)}>{s}</button>)}
              </div>
            : <div className="chips" role="group" aria-label={t.aria.examples}>
                {suggestions.map((s) => <button type="button" key={s} className="chip" disabled={busy} onClick={() => submit(s)}>{s}</button>)}
              </div>)}

          {ended
            ? <div className="session-ended" role="alert">
                <Icon name="schedule" size={26} />
                <div><strong>{t.session.expiredTitle}</strong><span className="muted small">{endedText}</span></div>
                <button type="button" className="btn btn-primary" onClick={onChangeCustomer}>{t.session.restart}</button>
              </div>
            : <form className="composer" onSubmit={(e) => { e.preventDefault(); submit(text, true) }}>
                <label htmlFor="composer-input" className="sr-only">{t.composer.label}</label>
                <input id="composer-input" ref={input} value={text} onChange={(e) => setText(e.target.value)}
                  placeholder={t.composer.placeholder} disabled={busy} autoComplete="off" />
                <button type="submit" className="btn btn-primary" disabled={busy || !text.trim()}>{t.composer.send}<Icon name="send" size={18} /></button>
              </form>}
        </section>

        <StepsPanel variant="rail" progress={stepProgress(turns)} trace={lastAssistant?.events ?? []} lang={lang} />
      </div>
    </>
  )
}

/** One turn. Assistant events are shown in the order the server streamed them; a verdict wraps the message that
 *  follows it, and a charge list shows which option the customer picked next. */
function TurnView({ turn, next, country, busy, onPick }:
  { turn: Turn; next: Turn | undefined; country: string; busy: boolean; onPick: (v: string) => void }) {
  const t = TEXT[turn.lang]
  const time = formatTime(turn.at, country)
  if (turn.role === 'customer') {
    return (
      <div className="msg customer" lang={turn.lang}>
        <div className="bubble">{turn.text}</div>
        <span className="msg-time">{time}</span>
      </div>
    )
  }
  const blocks: ReactNode[] = []
  const events = turn.events
  for (let i = 0; i < events.length; i++) {
    const e = events[i]
    switch (e.type) {
      case 'message':
        blocks.push(<div key={i} className="bubble-bot"><Statements text={e.text} statements={e.statements} lang={turn.lang} /></div>)
        break
      case 'verdict': {
        const m = events[i + 1]?.type === 'message' ? events[i + 1] as Extract<ChatEvent, { type: 'message' }> : null
        blocks.push(
          <VerdictCard key={i} verdict={e.verdict} lang={turn.lang}>
            {m && <Statements text={m.text} statements={m.statements} lang={turn.lang} />}
          </VerdictCard>,
        )
        if (m) i++
        break
      }
      case 'candidates': {
        const choice = next?.role === 'customer' ? Number(next.text?.trim()) : NaN
        const picked = e.items.some((c) => c.option === choice) ? choice : null
        blocks.push(<CandidateList key={i} items={e.items} lang={turn.lang} picked={picked} disabled={busy} onPick={onPick} />)
        break
      }
      case 'handoff':
        blocks.push(<CaseCard key={i} caseId={e.handoff.case_id} lang={turn.lang} time={time} />)
        break
      case 'error':
        // An ended session is shown once, in place of the composer.
        if (e.code !== 'session_expired' && e.code !== 'turn_limit') blocks.push(<div key={i} className="error-line">{e.text}</div>)
        break
      default:
        break
    }
  }
  if (!blocks.length) return null
  const done = events.some((e) => e.type === 'done')
  return (
    <div className="msg assistant" lang={turn.lang}>
      <span className="avatar navy" aria-hidden="true"><Icon name="account_balance" size={18} /></span>
      <div className="msg-body">
        {blocks}
        {done && <span className="msg-time">{time} · {t.assistant}</span>}
      </div>
    </div>
  )
}
