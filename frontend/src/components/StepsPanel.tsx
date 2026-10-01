import { useState } from 'react'
import type { ChatEvent, Lang, Progress } from '../api'
import { TEXT } from '../i18n'
import { Icon } from '../icons'

/** "How we review your case": where the customer's inquiry stands, as the workflow set it (specs/006). One list of
 *  customer stages per path (a charge, or a contact "from the bank"), the current one marked, and the outcome
 *  once it closes. A rail beside the chat on wide screens, a closed drawer on phones (specs/003, FR-210). The
 *  internal steps of the latest reply stay one tap away under the technical detail, for the demo. */
export function StepsPanel({ progress, trace, lang, variant }:
  { progress: Progress | null; trace: ChatEvent[]; lang: Lang; variant: 'rail' | 'drawer' }) {
  const t = TEXT[lang].steps
  const [open, setOpen] = useState(false)
  const path = t[progress?.path ?? 'charge']
  const outcome = progress?.done && progress.outcome ? t.outcomes[progress.outcome](progress.case) : null
  const list = (
    <>
      <ol className="steps">
        {path.names.map((name, i) => {
          const n = i + 1
          const state = !progress ? 'todo' : progress.done || n < progress.stage ? 'done' : n === progress.stage ? 'current' : 'todo'
          return (
            <li key={name} className={state} aria-current={state === 'current' ? 'step' : undefined}>
              <Icon name={state === 'done' ? 'check_circle' : state === 'current' ? 'radio_button_checked' : 'radio_button_unchecked'} />
              <span>
                <strong>{n}. {name}{state !== 'todo' && <span className="tag"> · {state === 'done' ? t.done : t.now}</span>}</strong>
                <span className="line">{path.lines[i]}</span>
              </span>
            </li>
          )
        })}
      </ol>
      {outcome && <p className="steps-outcome"><Icon name="flag" /> <strong>{outcome}</strong></p>}
    </>
  )
  const technical = (
    <details className="technical">
      <summary>{t.technical}</summary>
      <ol>
        {trace.filter((e) => e.type === 'step').map((e, i) => {
          const { type: _t, step, ...rest } = e as Extract<ChatEvent, { type: 'step' }>
          return <li key={i} lang="en"><strong>{String(step)}</strong> <code>{JSON.stringify(rest)}</code></li>
        })}
      </ol>
    </details>
  )
  const summary = !progress ? t.notStarted : outcome ?? t.progress(progress.stage, progress.total, path.names[progress.stage - 1])
  if (variant === 'rail') return (
    <aside className="panel steps-rail" aria-label={t.title}>
      <div><h2>{t.title}</h2><span className="muted small">{t.subtitle}</span></div>
      {list}
      {technical}
    </aside>
  )
  return (
    <section className="panel steps-drawer" aria-label={t.title}>
      <button type="button" className="drawer-toggle" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <Icon name="route" size={22} />
        <span><strong>{t.title}</strong><span className="muted">{summary}</span></span>
        <Icon name={open ? 'expand_less' : 'expand_more'} size={24} />
      </button>
      {open && <div className="drawer-body">{list}{technical}</div>}
    </section>
  )
}
