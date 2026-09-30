import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api, verifyTranscript, type Handoff, type Verification } from './api'
import { Icon, type IconName } from './icons'

// The specialist view is for bank staff and stays in Spanish (specs/003, FR-203).
const PRIORITY_ORDER = { urgent: 0, high: 1, normal: 2 } as const
const PRIORITY: Record<Handoff['priority'], { label: string; icon: IconName }> = {
  urgent: { label: 'Urgente', icon: 'priority_high' },
  high: { label: 'Alta', icon: 'arrow_upward' },
  normal: { label: 'Normal', icon: 'remove' },
}
const CASE_TYPE: Record<string, string> = {
  unrecognized_charge: 'Cargo no reconocido',
  fraud_suspected: 'Posible fraude',
  fake_contact_secret_shared: 'Posible estafa: compartió un código',
  compliance_review: 'Revisión de cumplimiento',
  technical_fallback: 'Falla técnica',
}

/** What the human specialist receives: a structured handoff, not a transcript. */
export function AgentQueue({ onGoToCustomer }: { onGoToCustomer: () => void }) {
  const { data, isLoading, error } = useQuery({ queryKey: ['handoffs'], queryFn: api.handoffs, refetchInterval: 3000 })
  const items = [...(data ?? [])].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
  return (
    <>
      <div className="spec-head">
        <h1>Casos para revisar</h1>
        {items.length > 0 && <p>{items.length} {items.length === 1 ? 'caso' : 'casos'} · ordenados por prioridad. Cada caso trae solo hechos verificados, no la conversación completa.</p>}
      </div>
      <div className="spec-grid">
        <VerifyPdf />
        <div className="queue">
          {isLoading && <p className="status-line" role="status">Cargando…</p>}
          {error && <p className="alert-block" role="alert">{String(error)}</p>}
          {data && !items.length && (
            <div className="panel empty">
              <Icon name="inbox" size={32} />
              <p>Sin casos todavía. Abra un reclamo desde el chat.</p>
              <button type="button" className="btn" onClick={onGoToCustomer}>Ir a la vista Cliente</button>
            </div>
          )}
          {items.map((h) => <HandoffCard key={h.case_id} h={h} />)}
        </div>
      </div>
    </>
  )
}

const RESULT: Record<Verification['result'], { label: string; tone: string; icon: IconName; text?: string }> = {
  match: { label: 'Coincide', tone: 'good', icon: 'task_alt' },
  altered: { label: 'Alterado', tone: 'bad', icon: 'difference', text: 'Este archivo cambió después de descargarse. Pida al cliente el PDF original.' },
  unknown_version: { label: 'Versión desconocida', tone: 'warn', icon: 'help', text: 'El PDF usa un formato que no reconocemos. Puede ser de otra versión de la app.' },
  unreadable: { label: 'No legible', tone: 'bad', icon: 'block', text: 'No pudimos leer este archivo. Pruebe con el PDF original.' },
}

/** Check a customer's transcript PDF against its check code (specs/002). Only the original file matches. */
function VerifyPdf() {
  const [result, setResult] = useState<Verification | null>(null)
  const [busy, setBusy] = useState(false)
  const [over, setOver] = useState(false)
  const onFile = async (file: File | undefined) => {
    if (!file) return
    setBusy(true)
    try { setResult(await verifyTranscript(file)) } catch { setResult({ result: 'unreadable' }) } finally { setBusy(false) }
  }
  const r = result && RESULT[result.result]
  return (
    <section className="panel verify-pdf" aria-labelledby="verify-title">
      <div>
        <h2 id="verify-title"><Icon name="verified" />Verificar PDF de conversación</h2>
        <span className="muted small">Solo el archivo original coincide. Una copia editada o guardada de nuevo aparece como alterada.</span>
      </div>
      <label className={`dropzone${over ? ' over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); void onFile(e.dataTransfer.files?.[0]) }}>
        <Icon name="upload_file" size={28} />
        <strong>Arrastre aquí el PDF del cliente</strong>
        <span className="muted small">o</span>
        <span className="btn">{busy ? 'Verificando…' : 'Elegir archivo'}</span>
        <input type="file" accept="application/pdf" disabled={busy} aria-label="Elegir el PDF del cliente"
          onChange={(e) => void onFile(e.target.files?.[0])} />
      </label>
      <div role="status">
        {result && r && (
          <div className={`result ${r.tone}`}>
            <Icon name={r.icon} size={22} />
            <div>
              <strong>{r.label}{result.result === 'altered' && result.check_code && <> · <span className="mono">{result.check_code}</span></>}</strong>
              {r.text && <span className="small">{r.text}</span>}
              {result.result === 'match' && (
                <dl>
                  {result.check_code && <><dt>Código</dt><dd className="mono">{result.check_code}</dd></>}
                  <dt>Registro</dt><dd>{result.registered ? 'Registrado' : 'No está en el registro actual'}</dd>
                  {result.case_ids && result.case_ids.length > 0 && <><dt>Casos</dt><dd className="mono">{result.case_ids.join(', ')}</dd></>}
                </dl>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

function HandoffCard({ h }: { h: Handoff }) {
  const p = PRIORITY[h.priority]
  return (
    <article className={`panel case ${h.priority}`} aria-labelledby={`case-${h.case_id}`}>
      <header>
        <span className={`priority ${h.priority}`}><Icon name={p.icon} size={16} />{p.label}</span>
        <span id={`case-${h.case_id}`} className="case-id">{h.case_id}</span>
        <span className="case-type">{CASE_TYPE[h.case_type] ?? h.case_type}</span>
        <span className="muted small">{h.created_at.replace('T', ' ').slice(0, 16)} · {h.language.toUpperCase()}</span>
      </header>
      <dl className="case-fields">
        <div><dt>Cliente</dt><dd>{h.customer.first_name} · {h.customer.country} · {h.customer.segment} · {h.language.toUpperCase()}</dd></div>
        {h.request && <div><dt>Solicitud</dt><dd>“{h.request}”</dd></div>}
        {h.customer_statement && <div><dt>Relato del cliente</dt><dd>“{h.customer_statement}”</dd></div>}
        {h.verified_facts && <div><dt>Hechos verificados</dt><dd><Facts facts={h.verified_facts} /></dd></div>}
        {h.card && <div><dt>Producto</dt><dd>{String(h.card.product_type)} ···{String(h.card.last4)} · {String(h.card.product_status)}</dd></div>}
        <div><dt>¿Compartió código?</dt><dd>
          {h.shared_secret === true ? <span className="shared-yes"><Icon name="warning" size={18} />Sí</span> : h.shared_secret === false ? 'No' : 'No indicado'}
        </dd></div>
        <div><dt>Acciones</dt><dd>{h.actions_taken.join(' · ')}</dd></div>
        {h.rights && <div><dt>Marco legal</dt><dd>{h.rights.join(', ')}{h.answer_by && <> · responder antes de <strong>{h.answer_by.slice(0, 10)}</strong></>}</dd></div>}
        {h.open_questions && h.open_questions.length > 0 && <div><dt>Preguntas abiertas</dt><dd><ul>{h.open_questions.map((q) => <li key={q}>{q}</li>)}</ul></dd></div>}
        <div><dt>Seguridad</dt><dd>
          {h.security_flags.length > 0
            ? <ul className="flags">{h.security_flags.map((f) => <li key={f}><Icon name="flag" size={16} />{f}</li>)}</ul>
            : <span className="no-flags"><Icon name="check" size={16} />Sin alertas</span>}
        </dd></div>
      </dl>
    </article>
  )
}

function Facts({ facts }: { facts: Record<string, string | number | null> }) {
  return (
    <div className="facts-wrap" tabIndex={0} role="region" aria-label="Hechos verificados">
      <table className="facts"><tbody>
        {Object.entries(facts).map(([k, v]) => <tr key={k}><th scope="row">{k}</th><td>{v ?? '—'}</td></tr>)}
      </tbody></table>
    </div>
  )
}
