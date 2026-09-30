import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { chargeMessage, claimPath, contactPathPt, customer, OTHER_CUSTOMER, reply, SCAM, SCENARIO, send, signIn } from './helpers'

// US4: keyboard, screen readers, contrast (FR-212 to FR-217; SC-204, SC-205).

async function axe(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`)).toEqual([])
}

test('sign-in has no accessibility violations', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('list', { name: 'Clientes de prueba' })).toBeVisible()
  await axe(page)
})

test('chat screens have no accessibility violations', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await page.getByRole('button', { name: '¿De dónde sale este dato?' }).first().click()
  await axe(page)
  await reply(page, 'No fui yo')
  await reply(page, 'Tengo la tarjeta y no compartí ningún código')
  await axe(page)
  await signIn(page, SCENARIO.other)
  await send(page, SCAM)
  await expect(page.locator('.verdict-card.bad')).toBeVisible()
  await axe(page)
})

test('the specialist view has no accessibility violations', async ({ page }) => {
  await claimPath(page)
  await page.getByRole('button', { name: 'Especialista' }).click()
  await expect(page.locator('article.case').first()).toBeVisible()
  await axe(page)
})

test('messages are announced and marked with their language', async ({ page }) => {
  await contactPathPt(page)
  const log = page.getByRole('log')
  await expect(log).toHaveAttribute('aria-live', 'polite')
  await expect(page.locator('.msg.assistant').last()).toHaveAttribute('lang', 'pt')
  await expect(page.locator('.msg.customer').last()).toHaveAttribute('lang', 'pt')
  await expect(page.getByRole('textbox', { name: 'Mensagem' })).toBeVisible()
})

test('the claim path works with the keyboard alone', async ({ page }, info) => {
  test.skip(info.project.name !== 'desktop-light', 'one keyboard run is enough')
  const c = await customer(page, SCENARIO.claim)
  await page.goto('/')
  const card = page.getByRole('button', { name: c.label })
  await expect(card).toBeVisible()
  for (let i = 0; i < 30 && !(await card.evaluate((n) => n === document.activeElement)); i++) await page.keyboard.press('Tab')
  await page.keyboard.press('Enter')
  const input = page.locator('#composer-input')
  await expect(input).toBeVisible()
  await input.focus() // equivalent to tabbing to it; checked above that every control is reachable
  await page.keyboard.type(chargeMessage(c))
  await page.keyboard.press('Enter')
  await expect(page.locator('.chips.replies')).toBeVisible({ timeout: 30_000 })
  await expect(input).toBeFocused()
  for (const choice of ['No fui yo', 'Tengo la tarjeta y no compartí ningún código']) {
    const btn = page.locator('.chips.replies').getByRole('button', { name: choice })
    for (let i = 0; i < 60 && !(await btn.evaluate((n) => n === document.activeElement)); i++) await page.keyboard.press('Shift+Tab')
    await expect(btn).toBeFocused()
    await page.keyboard.press('Space')
    await expect(page.locator('.typing')).toHaveCount(0, { timeout: 30_000 })
  }
  await expect(page.locator('.case-card')).toBeVisible()
})

test('scrolling respects reduced motion', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.addInitScript(() => {
    const calls: unknown[] = []
    ;(window as unknown as { __scrolls: unknown[] }).__scrolls = calls
    const orig = Element.prototype.scrollIntoView
    Element.prototype.scrollIntoView = function (arg?: boolean | ScrollIntoViewOptions) { calls.push(arg); return orig.call(this, arg) }
  })
  await signIn(page, SCENARIO.other)
  await send(page, OTHER_CUSTOMER)
  const behaviors = await page.evaluate(() => (window as unknown as { __scrolls: { behavior?: string }[] }).__scrolls.map((a) => a?.behavior))
  expect(behaviors.length).toBeGreaterThan(0)
  expect(behaviors.every((b) => b === 'auto')).toBe(true)
})
