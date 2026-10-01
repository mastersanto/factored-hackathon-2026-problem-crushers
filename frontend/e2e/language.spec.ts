import { expect, test } from '@playwright/test'
import { TEXT } from '../src/i18n'
import { chargeMessage, claimPath, contactPathPt, fixedTexts, otherThan, reply, showsText, SCENARIO, send, signIn, spanishOnly } from './helpers'

// US1: the whole chat in the customer's language (FR-201, FR-202, FR-215; SC-201).

test('a Portuguese conversation shows no Spanish fixed text', async ({ page }) => {
  await contactPathPt(page)
  await expect(page.locator('.verdict-card')).toContainText('Contato real do banco')
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt')
  const shown = await fixedTexts(page)
  const leaks = spanishOnly().filter((s) => shown.includes(s))
  expect(leaks, 'Spanish fixed texts in a Portuguese chat').toEqual([])
})

test('a Spanish conversation shows the Spanish texts', async ({ page }) => {
  await claimPath(page)
  await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  await expect(page.locator('.case-card')).toContainText('enviado a un especialista')
  await expect(page.locator('#composer-input')).toHaveAttribute('placeholder', /Escriba/)
})

test('before the first reply the texts are Spanish and invite both languages', async ({ page }) => {
  await signIn(page, SCENARIO.other)
  await expect(page.locator('html')).toHaveAttribute('lang', 'es')
  await expect(page.locator('.intro')).toContainText('português')
  await expect(page.locator('.intro')).toContainText('portugués')
})

// specs/004 US3: the app follows the language the customer writes in (FR-407, FR-408; SC-402).
test.describe('in an English browser', () => {
  test.use({ locale: 'en-US' })

  test('writing in Spanish switches the whole app to Spanish', async ({ page }) => {
    const c = await signIn(page, SCENARIO.claim, 'en')
    await expect(page.locator('.intro')).toContainText('You can write in English, Spanish, or Portuguese')
    await send(page, chargeMessage(c))
    await expect(page.locator('html')).toHaveAttribute('lang', 'es')
    await expect(page.getByRole('button', { name: TEXT.es.app.specialistTab })).toBeVisible()
    await expect(page.locator('.security-strip')).toContainText(TEXT.es.security)
    await expect(page.locator('#composer-input')).toHaveAttribute('placeholder', TEXT.es.composer.placeholder)
  })

  test('an English conversation shows no Spanish or Portuguese fixed text', async ({ page }) => {
    const c = await signIn(page, SCENARIO.claim, 'en')
    await send(page, `I don't recognize a charge of ${Number(c.hint.amount).toFixed(2)} at ${c.hint.merchant}`)
    await reply(page, "It wasn't me")
    await reply(page, "I have my card and didn't share any code")
    await expect(page.locator('.case-card')).toContainText('sent to a specialist')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    const shown = await fixedTexts(page)
    const leaks = otherThan('en').filter((s) => showsText(shown, s))
    expect(leaks, 'Spanish or Portuguese fixed texts in an English chat').toEqual([])
  })
})
