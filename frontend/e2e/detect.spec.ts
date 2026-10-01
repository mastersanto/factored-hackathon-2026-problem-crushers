import { expect, test, type Page } from '@playwright/test'
import type { Lang } from '../src/api'
import { TEXT } from '../src/i18n'

// specs/004 US1: the app opens in the browser's language, English when it offers none of the three
// (FR-402 to FR-404; SC-401). Each case overrides navigator.languages before the app's code runs, and records
// the first sign-in heading the moment it appears, to prove there is no flash of another language.

async function open(page: Page, languages: string[], stored?: string) {
  await page.addInitScript(([langs, choice]) => {
    Object.defineProperty(navigator, 'languages', { get: () => langs })
    Object.defineProperty(navigator, 'language', { get: () => langs[0] ?? '' })
    if (choice) window.localStorage.setItem('app-language', choice)
    const w = window as unknown as { __first?: { text: string; lang: string } }
    new MutationObserver((_, obs) => {
      const h1 = document.querySelector('h1')
      if (h1 && h1.textContent) {
        w.__first = { text: h1.textContent, lang: document.documentElement.lang }
        obs.disconnect()
      }
    }).observe(document, { childList: true, subtree: true })
  }, [languages, stored ?? ''] as const)
  await page.goto('/')
}

async function expectLanguage(page: Page, lang: Lang) {
  const t = TEXT[lang]
  await expect(page.locator('h1')).toHaveText(t.signIn.heading)
  await expect(page.locator('html')).toHaveAttribute('lang', lang)
  await expect(page.getByRole('list', { name: t.signIn.list })).toBeVisible()
  await expect(page.getByRole('button', { name: t.app.specialistTab })).toBeVisible()
  await expect(page.locator('.page-footer')).toHaveText(t.app.footer)
  // The first heading ever rendered was already in this language.
  const first = await page.evaluate(() => (window as unknown as { __first?: { text: string; lang: string } }).__first)
  expect(first).toEqual({ text: t.signIn.heading, lang })
}

const CASES: [string, string[], Lang][] = [
  ['English', ['en-US', 'en'], 'en'],
  ['Spanish (Mexico)', ['es-MX', 'es'], 'es'],
  ['Portuguese (Brazil)', ['pt-BR', 'pt'], 'pt'],
  ['French only', ['fr-FR', 'fr'], 'en'],
  ['French, then Spanish', ['fr-FR', 'es'], 'es'],
  ['Portuguese (Portugal), odd casing', ['PT-pt'], 'pt'],
  ['no preference at all', [], 'en'],
]

for (const [name, languages, lang] of CASES) {
  test(`browser ${name} opens in ${lang}`, async ({ page }) => {
    await open(page, languages)
    await expectLanguage(page, lang)
  })
}

test('a stored choice beats the browser', async ({ page }) => {
  await open(page, ['en-US', 'en'], 'pt')
  await expectLanguage(page, 'pt')
})

test('a broken stored value is ignored', async ({ page }) => {
  await open(page, ['es-AR'], 'klingon')
  await expectLanguage(page, 'es')
})

test('the specialist view follows the app language', async ({ page }) => {
  await open(page, ['en-US'])
  await page.getByRole('button', { name: TEXT.en.app.specialistTab }).click()
  await expect(page.locator('h1')).toHaveText(TEXT.en.specialist.title)
  await expect(page.getByRole('heading', { name: TEXT.en.specialist.verify.title })).toBeVisible()
})
