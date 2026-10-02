import { expect, test } from '@playwright/test'
import { chargeMessage, contactPathPt, reply, SCENARIO, send, signIn } from './helpers'

// US2: source labels in words, with a visible reference and an explainer (FR-204 to FR-207).

test('labels name their kind and show their reference as text', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  const chat = page.waitForResponse('**/api/chat')
  await send(page, chargeMessage(c))
  const body = await (await chat).text()
  const sources = body.split('\n').filter((l) => l.startsWith('data: ')).map((l) => JSON.parse(l.slice(6)))
    .filter((e) => e.type === 'message').flatMap((e) => e.statements.map((s: { source: string | null }) => s.source)).filter((s) => s && s !== 'flow')
  const log = page.getByRole('log')
  await expect(log.locator('.source-label', { hasText: 'VERIFICADO' }).first()).toBeVisible()
  // Every reference the server sent is on screen, exactly as sent (conversation lines, `flow`, have none).
  const refs = await log.locator('.source-ref').allTextContents()
  expect(refs).toEqual(expect.arrayContaining(sources))
  // No reference hides in a hover-only tooltip.
  await expect(log.locator('[title]')).toHaveCount(0)
  // A policy line (the claim checklist) is labelled as policy.
  await reply(page, 'No fui yo')
  await expect(log.locator('.source-label', { hasText: 'POLÍTICA' }).last()).toBeVisible()
  await expect(log.locator('.source-ref').last()).toHaveText('policy:handoff-checklist')
})

test('the explainer opens by keyboard, in the conversation language', async ({ page }) => {
  await contactPathPt(page)
  // The Portuguese reply re-shows the conversation in Portuguese (specs/004), which replaces the buttons: wait
  // until that is done, or the key press goes to a button that is about to be replaced.
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt')
  await page.waitForLoadState('networkidle')
  const toggle = page.getByRole('button', { name: 'De onde vem esta informação?' })
  await expect(async () => {
    await toggle.focus()
    await page.keyboard.press('Enter')
    await expect(toggle).toHaveAttribute('aria-expanded', 'true', { timeout: 1000 })
  }).toPass()
  const explain = page.locator('.sources-explain').first()
  await expect(explain.locator('dt')).toHaveCount(3)
  await expect(explain).toContainText('Estimativa')
})

test('conversation lines carry no label (a greeting, a re-asked question)', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, 'hola')
  const greeting = page.locator('.msg.assistant').last()
  await expect(greeting).toContainText(c.first_name.split(' ')[0])
  await expect(greeting.locator('.source-label')).toHaveCount(0)
  await expect(greeting.getByRole('button', { name: '¿De dónde sale este dato?' })).toHaveCount(0)
  await send(page, chargeMessage(c))
  await send(page, 'hola')
  const reask = page.locator('.msg.assistant').last()
  await expect(reask.locator('.source-label', { hasText: 'POLÍTICA' })).toHaveCount(1)  // the question's policy stays
  await expect(reask.locator('.source-ref')).toHaveText(['policy:close-needs-clear-yes'])
})
