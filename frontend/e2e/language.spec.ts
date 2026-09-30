import { expect, test } from '@playwright/test'
import { claimPath, contactPathPt, fixedTexts, SCENARIO, signIn, spanishOnly } from './helpers'

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
