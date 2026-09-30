import type { Basis, Lang } from '../api'
import { TEXT } from '../i18n'
import { Icon, type IconName } from '../icons'

const ICON: Record<Basis, IconName> = { known: 'check_circle', guessed: 'calculate', rule: 'policy' }

/** A statement's basis in words, never by colour alone (FR-204), and its reference as visible text exactly as
 *  the server sent it, not as a hover tooltip (FR-205, FR-207). No reference is shown when there is none. */
export function SourceLabel({ basis, source, lang }: { basis: Basis; source: string | null; lang: Lang }) {
  return (
    <span className="source">
      <span className={`source-label basis-${basis}`}><Icon name={ICON[basis]} size={14} />{TEXT[lang].basis[basis]}</span>
      {source && <><span className="sr-only">: </span><span className="source-ref">{source}</span></>}
    </span>
  )
}
