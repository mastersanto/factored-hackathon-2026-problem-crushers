import type { Lang } from '../api'
import { TEXT } from '../i18n'
import { Icon } from '../icons'

/** Shown when a case goes to a specialist. The customer's device receives only the case number (FR-219), so the
 *  card shows no case type (a compliance hold looks like any other case) and no dates: the deadline is in the
 *  labelled rule statement that follows, exactly as the server sent it (specs/003, R4). */
export function CaseCard({ caseId, lang, time }: { caseId: string; lang: Lang; time: string }) {
  const t = TEXT[lang].case
  return (
    <article className="case-card" aria-label={t.label(caseId)}>
      <div className="case-head">
        <span className="avatar"><Icon name="support_agent" size={22} /></span>
        <div><span className="muted small">{t.kicker}</span><span className="case-title">{t.sent(caseId)}</span></div>
      </div>
      <ol className="case-steps" aria-label={t.status}>
        <li className="done"><Icon name="check_circle" /><strong>{t.received}</strong><span className="muted">{time}</span></li>
        <li className="next"><Icon name="radio_button_checked" /><strong>{t.review}</strong><span>{t.reviewNote}</span></li>
        <li className="todo"><Icon name="radio_button_unchecked" /><strong>{t.answer}</strong><span>{t.answerNote}</span></li>
      </ol>
      <div className="case-keep">
        <span>{t.keep} <strong className="mono">{caseId}</strong></span>
        <span className="muted small">{t.pdfHint}</span>
      </div>
    </article>
  )
}
