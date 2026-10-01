import { createContext, useContext } from 'react'
import type { Lang } from './api'

// The app language (specs/004, research R9). It is decided once, before the first render, so the first text on
// screen is already in the final language (FR-404). Only the visitor's own choice is stored, on this device.

const LANGS: readonly Lang[] = ['en', 'es', 'pt']
const STORAGE_KEY = 'app-language'

function isLang(value: unknown): value is Lang {
  return typeof value === 'string' && (LANGS as readonly string[]).includes(value)
}

/** The stored choice, else the first browser preference whose primary subtag is en, es, or pt, else English
 *  (FR-402, FR-403). "es-MX", "ES-mx", and "es-419" are all Spanish; "fr-FR, es" is Spanish. */
export function pickLanguage(prefs: readonly string[], stored: string | null): Lang {
  if (isLang(stored)) return stored
  for (const pref of prefs) {
    const primary = pref.split('-')[0].trim().toLowerCase()
    if (isLang(primary)) return primary
  }
  return 'en'
}

/** The choice made with the switcher, if any. Never throws: storage can be blocked or unavailable. */
export function readStoredLanguage(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export function storeLanguage(lang: Lang): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // The choice still applies to this page; it just isn't remembered.
  }
}

export interface LanguageState { lang: Lang; setLang: (lang: Lang) => void }

export const LanguageContext = createContext<LanguageState>({ lang: 'en', setLang: () => {} })

export function useLanguage(): LanguageState {
  return useContext(LanguageContext)
}
