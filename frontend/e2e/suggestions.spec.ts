import { expect, test, type Page } from '@playwright/test'
import type { Lang } from '../src/api'
import { TEXT } from '../src/i18n'
import { claimPath, customer, noSideScroll, SCENARIO, send, signIn } from './helpers'

// specs/005: every suggestion in the language the customer is using (FR-501 to FR-507; SC-501, SC-503).

const LANGS: Lang[] = ['en', 'es', 'pt']
const NAMES = { en: 'English', es: 'Español', pt: 'Português' } as const

const examples = (page: Page, lang: Lang) => page.getByRole('group', { name: TEXT[lang].aria.examples }).getByRole('button')
const replies = (page: Page, lang: Lang) => page.getByRole('group', { name: TEXT[lang].aria.replies }).getByRole('button')

async function expectExamples(page: Page, lang: Lang, all: Record<Lang, string[]>) {
  await expect(examples(page, lang)).toHaveText(all[lang])
  for (const chip of await examples(page, lang).all()) await expect(chip).toHaveAttribute('lang', lang)
  const shown = await page.locator('main').innerText()
  for (const other of LANGS.filter((l) => l !== lang)) {
    for (const text of all[other].filter((t) => !all[lang].includes(t))) expect(shown, `${other} example in ${lang}`).not.toContain(text)
  }
}

for (const [locale, lang] of [['en-US', 'en'], ['es-MX', 'es'], ['pt-BR', 'pt']] as const) {
  test.describe(`a ${locale} browser`, () => {
    test.use({ locale })

    test('shows every example in its language only', async ({ page }) => {
      const c = await signIn(page, SCENARIO.claim, lang)
      await expectExamples(page, lang, c.examples)
    })
  })
}

test('the switcher replaces every example at once, before the first message', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.contact)
  for (const lang of ['en', 'pt', 'es'] as const) {
    await page.getByRole('button', { name: NAMES[lang] }).click()
    await expectExamples(page, lang, c.examples)
    if (isMobile) {
      await noSideScroll(page)
      for (const chip of await examples(page, lang).all()) expect((await chip.boundingBox())!.height).toBeGreaterThanOrEqual(44)
    }
  }
})

test.describe('tapping an example', () => {
  test.use({ locale: 'en-US' })

  test('keeps the language of the example', async ({ page }) => {
    const c = await signIn(page, SCENARIO.claim, 'en')
    const before = await page.locator('.msg.assistant .msg-time').count()
    await examples(page, 'en').first().click()
    await expect(page.locator('.msg.assistant .msg-time')).toHaveCount(before + 1, { timeout: 30_000 })
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.locator('.msg.assistant').last()).toContainText('The charge is for')
    expect(c.examples.en[0]).toContain('I don\'t recognize')
  })
})

test('quick replies follow the switcher at a question (US2)', async ({ page }) => {
  await signIn(page, SCENARIO.claim)
  const before = await page.locator('.msg.assistant .msg-time').count()
  await examples(page, 'es').first().click()
  await expect(page.locator('.msg.assistant .msg-time')).toHaveCount(before + 1, { timeout: 30_000 })
  await expect(replies(page, 'es')).toHaveText(['Sí, fui yo', 'No fui yo'])
  await page.getByRole('button', { name: NAMES.en }).click()
  await expect(replies(page, 'en')).toHaveText(['Yes, it was me', "It wasn't me"])
  for (const chip of await replies(page, 'en').all()) await expect(chip).toHaveAttribute('lang', 'en')
  await replies(page, 'en').filter({ hasText: "It wasn't me" }).click()
  await expect(page.locator('.msg.assistant').last()).toContainText('Tell me in your own words')
})

test('examples follow a language written after a case closes (US2)', async ({ page }) => {
  await claimPath(page)
  const c = await customer(page, SCENARIO.claim)
  await send(page, 'Obrigado, entendi')
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt')
  await expectExamples(page, 'pt', c.examples)
})
