import type { Candidate, Lang } from '../api'
import { TEXT } from '../i18n'
import { Icon } from '../icons'

/** The customer's matching charges. Picking one sends its option number, as before. */
export function CandidateList({ items, lang, picked, disabled, onPick }:
  { items: Candidate[]; lang: Lang; picked: number | null; disabled: boolean; onPick: (option: string) => void }) {
  const t = TEXT[lang].candidate
  return (
    <div className="candidates" role="group" aria-label={t.group}>
      {items.map((c) => {
        const state = picked === null ? '' : picked === c.option ? ' picked' : ' muted-card'
        return (
          <div key={c.option} className={`candidate${state}`}>
            <div className="cand-info">
              <strong>{c.merchant}</strong>
              <span className="mono">{c.when}</span>
              {c.status === 'Pending' && <span className="pending-tag">{t.pending}</span>}
            </div>
            <div className="cand-side">
              <span className="cand-amount">{c.amount}</span>
              {picked === null
                ? <button type="button" className="btn btn-primary" disabled={disabled}
                    aria-label={`${t.pick}: ${c.merchant}, ${c.amount}, ${c.when}`} onClick={() => onPick(String(c.option))}>{t.pick}</button>
                : picked === c.option && <span className="cand-picked"><Icon name="check_circle" />{t.picked}</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
