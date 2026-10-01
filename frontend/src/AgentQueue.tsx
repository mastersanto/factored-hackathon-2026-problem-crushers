import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api, verifyTranscript, type Handoff, type Verification } from './api'
import { TEXT } from './i18n'
import { Icon, type IconName } from './icons'
import { useLanguage } from './language'

// The specialist view follows the app language like every other screen (specs/004, FR-408). The customer's
// words, the verified facts, and IDs are shown as recorded.
const PRIORITY_ORDER = { urgent: 0, high: 1, normal: 2 } as const
const PRIORITY_ICON: Record<Handoff['priority'], IconName> = { urgent: 'priority_high', high: 'arrow_upward', normal: 'remove' }

/** What the human specialist receives: a structured handoff, not a transcript. */
export function AgentQueue({ onGoToCustomer }: { onGoToCustomer: () => void }) {
  const { lang } = useLanguage()
  const t = TEXT[lang].specialist
  const { data, isLoading, error } = useQuery({ queryKey: ['handoffs', lang], queryFn: () => api.handoffs(lang), refetchInterval: 3000 })
  const items = [...(data ?? [])].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
  return (
    <>
      <div className="spec-head">
        <h1>{t.title}</h1>
        {items.length > 0 && <p>{t.count(items.length)}</p>}
      </div>
      <div className="spec-grid">
        <VerifyPdf />
        <div className="queue">
          {isLoading && <p className="status-line" role="status">{t.loading}</p>}
          {error && <p className="alert-block" role="alert">{String(error)}</p>}
          {data && !items.length && (
            <div className="panel empty">
              <Icon name="inbox" size={32} />
              <p>{t.empty}</p>
              <button type="button" className="btn" onClick={onGoToCustomer}>{t.goToCustomer}</button>
            </div>
          )}
          {items.map((h) => <HandoffCard key={h.case_id} h={h} />)}
        </div>
      </div>
    </>
  )
}

const RESULT: Record<Verification['result'], { tone: string; icon: IconName }> = {
  match: { tone: 'good', icon: 'task_alt' },
  altered: { tone: 'bad', icon: 'difference' },
  unknown_version: { tone: 'warn', icon: 'help' },
  unreadable: { tone: 'bad', icon: 'block' },
}

/** Check a customer's transcript PDF against its check code (specs/002). Only the original file matches. */
function VerifyPdf() {
  const all = TEXT[useLanguage().lang].specialist
  const t = all.verify
  const [result, setResult] = useState<Verification | null>(null)
  const [busy, setBusy] = useState(false)
  const [over, setOver] = useState(false)
  const onFile = async (file: File | undefined) => {
    if (!file) return
    setBusy(true)
    try { setResult(await verifyTranscript(file)) } catch { setResult({ result: 'unreadable' }) } finally { setBusy(false) }
  }
  const r = result && { ...RESULT[result.result], ...all.result[result.result] }
  return (
    <section className="panel verify-pdf" aria-labelledby="verify-title">
      <div>
        <h2 id="verify-title"><Icon name="verified" />{t.title}</h2>
        <span className="muted small">{t.hint}</span>
      </div>
      <label className={`dropzone${over ? ' over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); void onFile(e.dataTransfer.files?.[0]) }}>
        <Icon name="upload_file" size={28} />
        <strong>{t.drop}</strong>
        <span className="muted small">{t.or}</span>
        <span className="btn">{busy ? t.checking : t.choose}</span>
        <input type="file" accept="application/pdf" disabled={busy} aria-label={t.input}
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
                  {result.check_code && <><dt>{t.code}</dt><dd className="mono">{result.check_code}</dd></>}
                  <dt>{t.registry}</dt><dd>{result.registered ? t.registered : t.notRegistered}</dd>
                  {result.case_ids && result.case_ids.length > 0 && <><dt>{t.cases}</dt><dd className="mono">{result.case_ids.join(', ')}</dd></>}
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
  const { lang } = useLanguage()
  const t = TEXT[lang].specialist
  const f = t.field
  const translated = (text?: string) => text && (
    <span className="case-translation" lang={lang}><Icon name="translate" size={14} />{TEXT[lang].reshow.translated}: “{text}”</span>
  )
  return (
    <article className={`panel case ${h.priority}`} aria-labelledby={`case-${h.case_id}`}>
      <header>
        <span className={`priority ${h.priority}`}><Icon name={PRIORITY_ICON[h.priority]} size={16} />{t.priority[h.priority]}</span>
        <span id={`case-${h.case_id}`} className="case-id">{h.case_id}</span>
        <span className="case-type">{t.caseType[h.case_type as keyof typeof t.caseType] ?? h.case_type}</span>
        <span className="muted small">{h.created_at.replace('T', ' ').slice(0, 16)} · {h.language.toUpperCase()}</span>
      </header>
      <dl className="case-fields">
        <div><dt>{f.customer}</dt><dd>{h.customer.first_name} · {h.customer.country} · {h.customer.segment} · {h.language.toUpperCase()}</dd></div>
        {h.request && <div><dt>{f.request}</dt><dd><span lang={h.language}>“{h.request}”</span>{translated(h.translations?.request)}</dd></div>}
        {h.customer_statement && <div><dt>{f.statement}</dt><dd><span lang={h.language}>“{h.customer_statement}”</span>{translated(h.translations?.customer_statement)}</dd></div>}
        {h.verified_facts && <div><dt>{f.facts}</dt><dd><Facts facts={h.verified_facts} label={f.facts} /></dd></div>}
        {h.card && <div><dt>{f.product}</dt><dd>{String(h.card.product_type)} ···{String(h.card.last4)} · {String(h.card.product_status)}</dd></div>}
        <div><dt>{f.shared}</dt><dd>
          {h.shared_secret === true ? <span className="shared-yes"><Icon name="warning" size={18} />{t.shared.yes}</span> : h.shared_secret === false ? t.shared.no : t.shared.unknown}
        </dd></div>
        <div><dt>{f.actions}</dt><dd>{h.actions_taken.join(' · ')}</dd></div>
        {h.rights && <div><dt>{f.legal}</dt><dd>{h.rights.join(', ')}{h.answer_by && <> · {f.answerBy} <strong>{h.answer_by.slice(0, 10)}</strong></>}</dd></div>}
        {h.open_questions && h.open_questions.length > 0 && <div><dt>{f.open}</dt><dd><ul>{h.open_questions.map((q) => <li key={q}>{q}</li>)}</ul></dd></div>}
        <div><dt>{f.security}</dt><dd>
          {h.security_flags.length > 0
            ? <ul className="flags">{h.security_flags.map((f) => <li key={f}><Icon name="flag" size={16} />{f}</li>)}</ul>
            : <span className="no-flags"><Icon name="check" size={16} />{t.noFlags}</span>}
        </dd></div>
      </dl>
    </article>
  )
}

function Facts({ facts, label }: { facts: Record<string, string | number | null>; label: string }) {
  return (
    <div className="facts-wrap" tabIndex={0} role="region" aria-label={label}>
      <table className="facts"><tbody>
        {Object.entries(facts).map(([k, v]) => <tr key={k}><th scope="row">{k}</th><td>{v ?? '—'}</td></tr>)}
      </tbody></table>
    </div>
  )
}
