import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Self-hosted fonts, Latin subset only: no third-party requests (specs/003, R8).
import '@fontsource/ibm-plex-sans/latin-400.css'
import '@fontsource/ibm-plex-sans/latin-500.css'
import '@fontsource/ibm-plex-sans/latin-600.css'
import '@fontsource/jetbrains-mono/latin-400.css'
import '@fontsource/jetbrains-mono/latin-600.css'
import App from './App.tsx'
import './index.css'
import { pickLanguage, readStoredLanguage } from './language'
import { LanguageRoot } from './LanguageRoot'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } })

// Decided before the first render (specs/004, FR-404): no text is ever shown in another language first.
const initialLang = pickLanguage(navigator.languages ?? [navigator.language], readStoredLanguage())
document.documentElement.lang = initialLang

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <LanguageRoot initial={initialLang}>
        <App />
      </LanguageRoot>
    </QueryClientProvider>
  </StrictMode>,
)
