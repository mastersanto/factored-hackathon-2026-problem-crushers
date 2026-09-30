import { useEffect, useRef, useState } from 'react'
import type { ChatEvent, Statement } from './api'
import { useChat, type Turn } from './useChat'

const BASIS_LABEL: Record<Statement['basis'], string> = { known: 'verificado', guessed: 'estimación', rule: 'política' }
const VERDICT: Record<string, { label: string; tone: string }> = {
  scam_asks_secret: { label: 'Estafa: pidió un código', tone: 'bad' },
  no_record: { label: 'Sin registro del banco', tone: 'warn' },
  bank_contact: { label: 'Contacto real del banco', tone: 'good' },
}

export function Chat({ sessionId, firstName, suggestions }: { sessionId: string; firstName: string; suggestions: string[] }) {
  const { turns, busy, stage, replies, send } = useChat(sessionId)
  const chips = replies ?? suggestions
  const [text, setText] = useState('')
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [turns])

  const submit = (value: string) => { void send(value); setText('') }
  const lastSteps = [...turns].reverse().find((t) => t.role === 'assistant')?.events.filter((e) => e.type === 'step') ?? []

  return (
    <div className="chat-layout">
      <section className="chat">
        <div className="messages">
          {turns.length === 0 && <p className="muted">Sesión iniciada como {firstName}. Escriba su consulta o use un ejemplo.</p>}
          {turns.map((t, i) => <TurnView key={i} turn={t} onPick={submit} />)}
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

function TurnView({ turn, onPick }: { turn: Turn; onPick: (v: string) => void }) {
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
            return <div key={i} className="handoff-note">Caso {e.handoff.case_id} enviado a un especialista · prioridad {e.handoff.priority}</div>
          case 'error':
            return <div key={i} className="verdict bad">{e.text}</div>
          default:
            return null
        }
      })}
    </div>
  )
}
