import { expect, test } from '@playwright/test'
import { chargeMessage, contactPathPt, SCENARIO, send, signIn } from './helpers'

// US2: source labels in words, with a visible reference and an explainer (FR-204 to FR-207).

test('labels name their kind and show their reference as text', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  const chat = page.waitForResponse('**/api/chat')
  await send(page, chargeMessage(c))
  const body = await (await chat).text()
  const sources = body.split('\n').filter((l) => l.startsWith('data: ')).map((l) => JSON.parse(l.slice(6)))
    .filter((e) => e.type === 'message').flatMap((e) => e.statements.map((s: { source: string | null }) => s.source)).filter(Boolean)
  const log = page.getByRole('log')
  await expect(log.locator('.source-label', { hasText: 'VERIFICADO' }).first()).toBeVisible()
  await expect(log.locator('.source-label', { hasText: 'POLÍTICA' }).first()).toBeVisible()
  // Every reference the server sent is on screen, exactly as sent.
  const refs = await log.locator('.source-ref').allTextContents()
  expect(refs).toEqual(expect.arrayContaining(sources))
  // No reference hides in a hover-only tooltip.
  await expect(log.locator('[title]')).toHaveCount(0)
})

test('the explainer opens by keyboard, in the conversation language', async ({ page }) => {
  await contactPathPt(page)
  const toggle = page.getByRole('button', { name: 'De onde vem esta informação?' })
  await toggle.focus()
  await page.keyboard.press('Enter')
  await expect(toggle).toHaveAttribute('aria-expanded', 'true')
  const explain = page.locator('.sources-explain').first()
  await expect(explain.locator('dt')).toHaveCount(3)
  await expect(explain).toContainText('Estimativa')
})
