import { defineConfig } from '@playwright/test'

// UI acceptance checks (specs/003, research R9). Run `make dev` first, in rules mode: the checks
// drive the real app against the local API, at desktop and phone width, in light and dark themes.
// Every existing check runs in a Spanish (Mexico) browser: the app's language now follows the browser (specs/004, R13).
const desktop = { viewport: { width: 1200, height: 900 }, locale: 'es-MX' }
const phone = { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, locale: 'es-MX' }

export default defineConfig({
  testDir: 'e2e',
  outputDir: 'test-results',
  workers: 1,
  retries: 0,
  timeout: 60_000,
  use: { baseURL: 'http://localhost:5173' },
  projects: [
    { name: 'desktop-light', use: { ...desktop, colorScheme: 'light' } },
    { name: 'desktop-dark', use: { ...desktop, colorScheme: 'dark' } },
    { name: 'phone-light', use: { ...phone, colorScheme: 'light' } },
    { name: 'phone-dark', use: { ...phone, colorScheme: 'dark' } },
  ],
})
