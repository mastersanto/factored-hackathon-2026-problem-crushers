import { expect, test } from '@playwright/test'
import { SCENARIO, customer } from './helpers'

// Sign-in must say why it failed instead of doing nothing. The API is stubbed, so the real
// per-visitor session limit is never touched.

test('sign-in explains the session limit (429)', async ({ page }) => {
  const c = await customer(page, SCENARIO.other)
  await page.route('**/api/session', (r) => r.fulfill({ status: 429, json: { detail: 'too many sessions; try again later' } }))
  await page.goto('/')
  await page.getByRole('button', { name: c.label }).click()
  await expect(page.getByRole('alert')).toContainText('demasiadas conversaciones')
  await expect(page.getByRole('button', { name: c.label })).toBeEnabled()
})

test('sign-in explains other failures', async ({ page }) => {
  const c = await customer(page, SCENARIO.other)
  await page.route('**/api/session', (r) => r.abort())
  await page.goto('/')
  await page.getByRole('button', { name: c.label }).click()
  await expect(page.getByRole('alert')).toContainText('No pudimos abrir la conversación')
  await page.unroute('**/api/session')
  await page.getByRole('button', { name: c.label }).click()
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.locator('#composer-input')).toBeVisible()
})
