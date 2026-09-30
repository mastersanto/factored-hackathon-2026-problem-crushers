import { useEffect, useRef, useState } from 'react'
import { downloadTranscript, HttpError, type ChatEvent, type Lang, type Statement } from './api'
import { useChat, type Turn } from './useChat'

const BASIS_LABEL: Record<Statement['basis'], string> = { known: 'verificado', guessed: 'estimación', rule: 'política' }
const VERDICT: Record<string, { label: string; tone: string }> = {
  scam_asks_secret: { label: 'Estafa: pidió un código', tone: 'bad' },
  no_record: { label: 'Sin registro del banco', tone: 'warn' },
  bank_contact: { label: 'Contacto real del banco', tone: 'good' },
}

// Transcript download texts, following the language of the latest reply (specs/002, FR-109).
const PDF_TEXT: Record<Lang, { button: string; saved: string; expired: string; failed: string; hint: string }> = {
  es: { button: 'Descargar conversación (PDF)', saved: 'Descargado · código de verificación', expired: 'Sesión expirada; inicie sesión de nuevo',
        failed: 'No se pudo generar el PDF', hint: 'Puede descargar una copia de esta conversación' },
  pt: { button: 'Baixar conversa (PDF)', saved: 'Baixado · código de verificação', expired: 'Sessão expirada; entre novamente',
        failed: 'Não foi possível gerar o PDF', hint: 'Você pode baixar uma cópia desta conversa' },
}

export function Chat({ sessionId, conversationRef, firstName, suggestions }:
  { sessionId: string; conversationRef: string; firstName: string; suggestions: string[] }) {
  const { turns, busy, stage, replies, lang, completed, send } = useChat(sessionId)
  const [pdf, setPdf] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null)
  const t = PDF_TEXT[lang]
  const download = async () => {
    try {
      const code = await downloadTranscript(sessionId, conversationRef)
      setPdf({ tone: 'good', text: `${t.saved}: ${code}` })
    } catch (err) {
      setPdf({ tone: 'bad', text: err instanceof HttpError && err.status === 401 ? t.expired : `${t.failed} (${String(err)})` })
    }
  }
  const chips = replies ?? suggestions
  const [text, setText] = useState('')
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [turns])

  const submit = (value: string) => { void send(value); setText('') }
  const lastSteps = [...turns].reverse().find((t) => t.role === 'assistant')?.events.filter((e) => e.type === 'step') ?? []

  return (
    <div className="chat-layout">
      <section className="chat">
        <div className="chat-tools">
          <button className="link" disabled={busy || !completed} onClick={() => void download()}>{t.button}</button>
          {pdf && <span className={`small ${pdf.tone}`}>{pdf.text}</span>}
        </div>
        <div className="messages">
          {turns.length === 0 && <p className="muted">Sesión iniciada como {firstName}. Escriba su consulta o use un ejemplo.</p>}
          {turns.map((turn, i) => <TurnView key={i} turn={turn} onPick={submit} hint={t.hint} />)}
          {busy && <div className="typing">…</div>}
          <div ref={end} />
        </div>
        <div className={`suggestions${replies ? ' replies' : ''}`}>
          {chips.map((s) => <button key={s} className="chip" disabled={busy} onClick={() => submit(s)}>{s}</button>)}
        </div>
        <form className="composer" onSubmit={(e) => { e.preventDefault(); submit(text) }}>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Escriba en español o português…" disabled={busy} />
          <button type="submit" disabled={busy || !text.trim()}>Enviar</button>
        </form>
      </section>
      <aside className="trace">
        <h3>Flujo del último turno</h3>
        <p className="muted small">etapa: {stage}</p>
        <ol>
          {lastSteps.map((e, i) => {
            const { type: _t, step, ...rest } = e as Extract<ChatEvent, { type: 'step' }>
            return <li key={i}><strong>{String(step)}</strong> <code>{JSON.stringify(rest)}</code></li>
          })}
        </ol>
      </aside>
    </div>
  )
}

function TurnView({ turn, onPick, hint }: { turn: Turn; onPick: (v: string) => void; hint: string }) {
  if (turn.role === 'customer') return <div className="bubble customer">{turn.text}</div>
  return (
    <div className="assistant">
      {turn.events.map((e, i) => {
        switch (e.type) {
          case 'message':
            return (
              <div key={i} className="bubble bot">
                <p>{e.text}</p>
                <ul className="statements">
                  {e.statements.map((s, j) => (
                    <li key={j} className={`basis-${s.basis}`} title={s.source ?? ''}>
                      <span className="badge">{BASIS_LABEL[s.basis]}</span>{s.source && <span className="source">{s.source}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )
          case 'candidates':
            return (
              <div key={i} className="candidates">
                {e.items.map((c) => (
                  <button key={c.option} onClick={() => onPick(String(c.option))}>
                    <strong>{c.option}.</strong> {c.amount} · {c.merchant} · {c.when} {c.status === 'Pending' && <em>(pendiente)</em>}
                  </button>
                ))}
              </div>
            )
          case 'verdict':
            return <div key={i} className={`verdict ${VERDICT[e.verdict].tone}`}>{VERDICT[e.verdict].label}</div>
          case 'handoff':
            return <div key={i} className="handoff-note">Caso {e.handoff.case_id} enviado a un especialista<br /><span className="muted small">{hint}</span></div>
          case 'error':
            return <div key={i} className="verdict bad">{e.text}</div>
          default:
            return null
        }
      })}
    </div>
  )
}
