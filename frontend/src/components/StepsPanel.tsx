import { useState } from 'react'
import type { ChatEvent, Lang } from '../api'
import { TEXT } from '../i18n'
import { Icon } from '../icons'

/** "How we review your case": the five workflow steps in plain words, with the furthest step of the latest turn
 *  marked (specs/003, R3). A rail beside the chat on wide screens, a closed drawer on phones (FR-210). The raw
 *  trace stays one tap away for the demo; internal steps never reach the browser. */
export function StepsPanel({ progress, trace, lang, variant }:
  { progress: number | null; trace: ChatEvent[]; lang: Lang; variant: 'rail' | 'drawer' }) {
  const t = TEXT[lang].steps
  const [open, setOpen] = useState(false)
  const list = (
    <ol className="steps">
      {t.names.map((name, i) => {
        const state = progress === null || i > progress ? 'todo' : i < progress ? 'done' : 'current'
        return (
          <li key={name} className={state} aria-current={state === 'current' ? 'step' : undefined}>
            <Icon name={state === 'done' ? 'check_circle' : state === 'current' ? 'radio_button_checked' : 'radio_button_unchecked'} />
            <span>
              <strong>{i + 1}. {name}{state !== 'todo' && <span className="tag"> · {state === 'done' ? t.done : t.now}</span>}</strong>
              <span className="line">{t.lines[i]}</span>
            </span>
          </li>
        )
      })}
    </ol>
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
  const summary = progress === null ? t.notStarted : t.progress(progress + 1, t.names[progress])
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
