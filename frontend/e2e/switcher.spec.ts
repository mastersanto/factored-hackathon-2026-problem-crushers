import { expect, test, type Page } from '@playwright/test'
import { TEXT } from '../src/i18n'
import { claimPath, noSideScroll } from './helpers'

// specs/004 US4: the ES / PT / EN switcher (FR-405, FR-406; contracts/ui.md).

const NAMES = { en: 'English', es: 'Español', pt: 'Português' } as const

async function pick(page: Page, lang: keyof typeof NAMES) {
  await page.getByRole('button', { name: NAMES[lang] }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', lang)
  await expect(page.getByRole('button', { name: NAMES[lang] })).toHaveAttribute('aria-pressed', 'true')
}

test('every screen switches at once, and the choice survives a reload', async ({ page }) => {
  await page.goto('/')
  await pick(page, 'en')
  await expect(page.locator('h1')).toHaveText(TEXT.en.signIn.heading)
  await pick(page, 'pt')
  await expect(page.locator('h1')).toHaveText(TEXT.pt.signIn.heading)
  await page.getByRole('button', { name: TEXT.pt.app.specialistTab }).click()
  await expect(page.locator('h1')).toHaveText(TEXT.pt.specialist.title)
  await pick(page, 'en')
  await expect(page.locator('h1')).toHaveText(TEXT.en.specialist.title)
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')         // es-MX browser, stored choice wins
  await expect(page.getByRole('button', { name: NAMES.en })).toHaveAttribute('aria-pressed', 'true')
})

test('during a conversation the switcher re-shows it and keeps the unsent text', async ({ page }) => {
  await claimPath(page)
  await page.locator('#composer-input').fill('texto sin enviar')
  await pick(page, 'en')
  await expect(page.locator('.msg.assistant').first()).toContainText('The charge is for')
  await expect(page.locator('.case-card')).toContainText('sent to a specialist')
  await expect(page.locator('#composer-input')).toHaveValue('texto sin enviar')
  await expect(page.getByRole('button', { name: NAMES.en })).toBeFocused()
  await pick(page, 'es')
  await expect(page.locator('.msg.assistant').first()).toContainText('El cargo es de')
})

test('spoken names, pressed state, tap targets, and phone width', async ({ page }) => {
  await page.goto('/')
  const group = page.getByRole('group', { name: 'Idioma' })  // the projects run in es-MX
  await expect(group).toBeVisible()
  for (const [lang, name] of Object.entries(NAMES)) {
    const b = page.getByRole('button', { name })
    await expect(b).toHaveAttribute('lang', lang)
    const box = (await b.boundingBox())!
    expect(box.width).toBeGreaterThanOrEqual(44)
    expect(box.height).toBeGreaterThanOrEqual(44)
  }
  await expect(page.getByRole('button', { name: NAMES.es })).toHaveAttribute('aria-pressed', 'true')
  await noSideScroll(page)
  await pick(page, 'pt')
  await noSideScroll(page)
})
