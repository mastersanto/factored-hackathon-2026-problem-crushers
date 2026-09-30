import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api, verifyTranscript, type Handoff, type Verification } from './api'

const PRIORITY_ORDER = { urgent: 0, high: 1, normal: 2 } as const

/** What the human specialist receives: a structured handoff, not a transcript. */
export function AgentQueue() {
  return <><VerifyPdf /><Queue /></>
}

function Queue() {
  const { data, isLoading, error } = useQuery({ queryKey: ['handoffs'], queryFn: api.handoffs, refetchInterval: 3000 })
  if (isLoading) return <p className="muted">Cargando…</p>
  if (error) return <p className="verdict bad">{String(error)}</p>
  const items = [...(data ?? [])].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
  if (!items.length) return <p className="muted">Sin casos todavía. Abra un reclamo desde el chat.</p>
  return <div className="queue">{items.map((h) => <HandoffCard key={h.case_id} h={h} />)}</div>
}

const RESULT: Record<Verification['result'], { label: string; tone: string }> = {
  match: { label: 'Coincide', tone: 'good' },
  altered: { label: 'Alterado', tone: 'bad' },
  unknown_version: { label: 'Versión desconocida', tone: 'warn' },
  unreadable: { label: 'No legible', tone: 'bad' },
}

/** Check a customer's transcript PDF against its check code (specs/002). Only the original file matches. */
function VerifyPdf() {
  const [result, setResult] = useState<Verification | null>(null)
  const [busy, setBusy] = useState(false)
  const onFile = async (file: File | undefined) => {
    if (!file) return
    setBusy(true)
    try { setResult(await verifyTranscript(file)) } catch { setResult({ result: 'unreadable' }) } finally { setBusy(false) }
  }
  const r = result && RESULT[result.result]
  return (
    <div className="verify">
      <label><strong>Verificar PDF de conversación</strong>{' '}
        <input type="file" accept="application/pdf" disabled={busy} onChange={(e) => void onFile(e.target.files?.[0])} />
      </label>
      {result && r && (
        <div className={`verdict ${r.tone}`}>
          {r.label}
          {result.check_code && <> · {result.check_code}</>}
          {result.result === 'match' && <> · {result.registered ? 'registrado' : 'no está en el registro actual'}
            {result.case_ids && result.case_ids.length > 0 && <> · {result.case_ids.join(', ')}</>}</>}
        </div>
      )}
    </div>
  )
}

function HandoffCard({ h }: { h: Handoff }) {
  return (
    <article className={`card priority-${h.priority}`}>
      <header>
        <strong>{h.case_id}</strong>
        <span className={`pill ${h.priority}`}>{h.priority}</span>
        <span className="pill">{h.case_type}</span>
        <span className="muted small">{h.created_at}</span>
      </header>
      <dl>
        <dt>Cliente</dt><dd>{h.customer.first_name} · {h.customer.country} · {h.customer.segment} · {h.language.toUpperCase()}</dd>
        {h.request && <><dt>Solicitud</dt><dd>“{h.request}”</dd></>}
        {h.customer_statement && <><dt>Relato del cliente</dt><dd>“{h.customer_statement}”</dd></>}
        {h.verified_facts && <><dt>Hechos verificados</dt><dd><Facts facts={h.verified_facts} /></dd></>}
        {h.card && <><dt>Producto</dt><dd>{String(h.card.product_type)} ···{String(h.card.last4)} · {String(h.card.product_status)}</dd></>}
        <dt>¿Compartió código?</dt><dd>{h.shared_secret === true ? 'sí' : h.shared_secret === false ? 'no' : 'no indicado'}</dd>
        <dt>Acciones</dt><dd>{h.actions_taken.join(' · ')}</dd>
        {h.rights && <><dt>Marco legal</dt><dd>{h.rights.join(', ')}{h.answer_by && <> · responder antes de <strong>{h.answer_by.slice(0, 10)}</strong></>}</dd></>}
        {h.open_questions && h.open_questions.length > 0 && <><dt>Preguntas abiertas</dt><dd><ul>{h.open_questions.map((q) => <li key={q}>{q}</li>)}</ul></dd></>}
        {h.security_flags.length > 0 && <><dt>Seguridad</dt><dd className="bad">{h.security_flags.join(', ')}</dd></>}
      </dl>
    </article>
  )
}

function Facts({ facts }: { facts: Record<string, string | number | null> }) {
  return (
    <table className="facts"><tbody>
      {Object.entries(facts).map(([k, v]) => <tr key={k}><th>{k}</th><td>{v ?? '—'}</td></tr>)}
    </tbody></table>
  )
}
