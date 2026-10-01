import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { TEXT } from '../src/i18n'
import { noSideScroll, SCENARIO, send, signIn } from './helpers'

// specs/007: answers that react to what the customer asks (the last movements, courtesy, help).

test('"my last movements" shows them as cards, and picking one explains it', async ({ page, isMobile }) => {
  await signIn(page, SCENARIO.other)
  await send(page, 'Muéstrame mis últimos movimientos')
  const group = page.getByRole('group', { name: TEXT.es.candidate.group }).last()
  const cards = group.locator('.candidate')
  const n = await cards.count()
  expect(n).toBeGreaterThan(0)
  expect(n).toBeLessThanOrEqual(5)
  await expect(page.locator('.msg.assistant').last()).toContainText(`Estos son sus últimos ${n} movimientos`)
  if (isMobile) await noSideScroll(page)
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(violations.map((v) => v.id)).toEqual([])
  const before = await page.locator('.msg.assistant .msg-time').count()
  await group.getByRole('button').first().click()
  await expect(page.locator('.msg.assistant .msg-time')).toHaveCount(before + 1, { timeout: 30_000 })
  await expect(page.locator('.msg.assistant').last()).toContainText(/El (cargo|movimiento) es|especialista/)
})

test('the examples include "my last movements"', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  expect(c.examples.es).toContain('Muéstrame mis últimos movimientos')
  await expect(page.getByRole('group', { name: TEXT.es.aria.examples }).getByRole('button', { name: 'Muéstrame mis últimos movimientos' })).toBeVisible()
})

test('thanks and help get their own answer', async ({ page }) => {
  await signIn(page, SCENARIO.other)
  await send(page, 'gracias')
  await expect(page.locator('.msg.assistant').last()).toContainText('Con gusto')
  await send(page, '¿qué puedes hacer?')
  await expect(page.locator('.msg.assistant').last()).toContainText('Puedo mostrarle sus últimos movimientos')
})
