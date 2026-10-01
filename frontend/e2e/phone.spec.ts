import { expect, test, type Page } from '@playwright/test'
import { TEXT } from '../src/i18n'
import { chargeMessage, claimPath, contactPathPt, noSideScroll, SCENARIO, send, signIn } from './helpers'

// US3: use it on a phone (FR-208 to FR-211; SC-203). Phone projects only.

test.beforeEach(({ isMobile }) => { test.skip(!isMobile, 'phone width only') })

async function tapTargets(page: Page) {
  const small = await page.evaluate(() => [...document.querySelectorAll('button, a, input, [role=button]')]
    .filter((n) => (n as HTMLElement).offsetParent !== null && !(n.closest('.dropzone') && n.tagName === 'INPUT'))
    .map((n) => { const r = n.getBoundingClientRect(); return { what: (n.textContent || n.getAttribute('aria-label') || n.tagName).trim().slice(0, 40), w: r.width, h: r.height } })
    .filter((r) => r.w < 44 || r.h < 44))
  expect(small, 'controls smaller than 44 × 44 px').toEqual([])
}

test('sign-in fits and has large targets', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('list', { name: 'Clientes de prueba' })).toBeVisible()
  await noSideScroll(page)
  await tapTargets(page)
})

test('the claim path fits, and the text box stays in view', async ({ page }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await expect(page.locator('#composer-input')).toBeInViewport()
  await noSideScroll(page)
  await tapTargets(page)
  const drawer = page.locator('.drawer-toggle')
  await expect(drawer).toHaveAttribute('aria-expanded', 'false')
  await drawer.click()
  await expect(drawer).toHaveAttribute('aria-expanded', 'true')
  await noSideScroll(page)
  await claimPath(page)
  await noSideScroll(page)
})

test('the call check and the specialist view fit', async ({ page }) => {
  await contactPathPt(page)
  await noSideScroll(page)
  await page.getByRole('button', { name: 'Especialista', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Casos para revisar' })).toBeVisible()
  await noSideScroll(page)
  await tapTargets(page)
})

// specs/004 US1: English texts fit too (SC-408).
test.describe('in English', () => {
  test.use({ locale: 'en-US' })

  test('sign-in and the specialist view fit, with large targets', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('list', { name: TEXT.en.signIn.list })).toBeVisible()
    await noSideScroll(page)
    await tapTargets(page)
    await page.getByRole('button', { name: TEXT.en.app.specialistTab }).click()
    await expect(page.getByRole('heading', { name: TEXT.en.specialist.title })).toBeVisible()
    await noSideScroll(page)
  })
})
