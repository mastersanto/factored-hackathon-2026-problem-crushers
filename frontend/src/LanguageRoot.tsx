import { useMemo, useState, type ReactNode } from 'react'
import type { Lang } from './api'
import { LanguageContext } from './language'

/** Holds the app language for the whole tree (specs/004). The initial value is decided before the first render. */
export function LanguageRoot({ initial, children }: { initial: Lang; children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(initial)
  const value = useMemo(() => ({ lang, setLang }), [lang])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}
