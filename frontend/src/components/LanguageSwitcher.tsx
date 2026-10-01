import type { Lang } from '../api'

// The ES / PT / EN switcher (specs/004, US4; contracts/ui.md). Each option's spoken name is in its own language,
// and the current one is marked as pressed, so a screen reader announces it.
const OPTIONS: { lang: Lang; short: string; name: string }[] = [
  { lang: 'es', short: 'ES', name: 'Español' },
  { lang: 'pt', short: 'PT', name: 'Português' },
  { lang: 'en', short: 'EN', name: 'English' },
]

const GROUP_NAME: Record<Lang, string> = { en: 'Language', es: 'Idioma', pt: 'Idioma' }

export function LanguageSwitcher({ lang, onPick }: { lang: Lang; onPick: (lang: Lang) => void }) {
  return (
    <div className="lang-switcher" role="group" aria-label={GROUP_NAME[lang]}>
      {OPTIONS.map((o) => (
        <button key={o.lang} type="button" lang={o.lang} aria-label={o.name} aria-pressed={o.lang === lang}
          onClick={() => { if (o.lang !== lang) onPick(o.lang) }}>
          {o.short}
        </button>
      ))}
    </div>
  )
}
