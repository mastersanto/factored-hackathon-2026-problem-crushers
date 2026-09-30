import type { ReactNode } from 'react'
import type { ChatEvent, Lang } from '../api'
import { TEXT } from '../i18n'
import { Icon, type IconName } from '../icons'

type Verdict = Extract<ChatEvent, { type: 'verdict' }>['verdict']
const LOOK: Record<Verdict, { tone: string; icon: IconName }> = {
  bank_contact: { tone: 'good', icon: 'verified_user' },
  no_record: { tone: 'warn', icon: 'help' },
  scam_asks_secret: { tone: 'bad', icon: 'gpp_bad' },
}

/** The answer to "was it really my bank?". The title maps the deterministic verdict code to a fixed text; every
 *  fact comes from the message statements passed as children. */
export function VerdictCard({ verdict, lang, children }: { verdict: Verdict; lang: Lang; children?: ReactNode }) {
  const look = LOOK[verdict]
  return (
    <div role="status" className={`verdict-card ${look.tone}`}>
      <Icon name={look.icon} size={26} />
      <div className="vc-body">
        <span className="vc-title">{TEXT[lang].verdict[verdict]}</span>
        {children}
      </div>
    </div>
  )
}
