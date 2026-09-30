import { useId, useState } from 'react'
import type { Lang, Statement } from '../api'
import { TEXT } from '../i18n'
import { Icon } from '../icons'
import { SourceLabel } from './SourceLabel'

/** An assistant message and the basis of each statement in it (specs/003, R2).
 *  With template wording the message text is exactly the statements joined, so each statement is shown on its
 *  own line with its label. When Claude reworded the message (after the faithfulness check), the reworded text is
 *  shown as it is, followed by the list of sources. Either way the customer reads exactly the text the server
 *  streamed, which is also what the transcript PDF records. */
export function Statements({ text, statements, lang }: { text: string; statements: Statement[]; lang: Lang }) {
  const t = TEXT[lang]
  const [open, setOpen] = useState(false)
  const id = useId()
  const perStatement = statements.length > 0 && text === statements.map((s) => s.text).join(' ')
  return (
    <>
      {perStatement ? (
        <ul className="statements">
          {statements.map((s, i) => (
            <li key={i}><span>{s.text}</span><SourceLabel basis={s.basis} source={s.source} lang={lang} /></li>
          ))}
        </ul>
      ) : (
        <>
          <p>{text}</p>
          {statements.length > 0 && <>
            <p className="sources-title">{t.sources.title}</p>
            <ul className="source-list">
              {statements.map((s, i) => <li key={i}><SourceLabel basis={s.basis} source={s.source} lang={lang} /></li>)}
            </ul>
          </>}
        </>
      )}
      {statements.length > 0 && <>
        <button type="button" className="link-btn sources-toggle" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}>
          <Icon name="info" size={18} />{t.sources.toggle}
        </button>
        <dl id={id} className="sources-explain" hidden={!open}>
          {(['known', 'guessed', 'rule'] as const).map((b) => (
            <div key={b}><dt className={`basis-${b}`}>{t.basisTerm[b]}</dt><dd>{t.basisExplain[b]}</dd></div>
          ))}
        </dl>
      </>}
    </>
  )
}
