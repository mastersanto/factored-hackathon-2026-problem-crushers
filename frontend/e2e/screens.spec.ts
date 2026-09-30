import { expect, test } from '@playwright/test'
import { chargeMessage, claimPath, contactPathPt, noSideScroll, OTHER_CUSTOMER, SCAM, SCENARIO, send, shot, signIn } from './helpers'

// Reference screenshots for comparison with the approved prototype (specs/003-ui-improvements/design/).
// Saved to e2e/screenshots/{project}/, git-ignored: they show synthetic organizer rows.

test('reference screenshots', async ({ page }, info) => {
  await page.goto('/')
  await expect(page.getByRole('list', { name: 'Clientes de prueba' })).toBeVisible()
  await shot(page, info, '1-sign-in')

  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await page.getByRole('button', { name: '¿De dónde sale este dato?' }).first().click()
  await shot(page, info, '2a-charge-explained')
  await claimPath(page)
  await shot(page, info, '2b-case-sent')

  await contactPathPt(page)
  await shot(page, info, '2c-bank-contact-pt')

  await signIn(page, SCENARIO.other)
  await send(page, SCAM)
  await shot(page, info, '2d-scam')

  await signIn(page, SCENARIO.other)
  await send(page, OTHER_CUSTOMER)
  await shot(page, info, '2e-refusal')

  await page.getByRole('button', { name: 'Especialista' }).click()
  await expect(page.locator('article.case').first()).toBeVisible()
  await noSideScroll(page)
  await shot(page, info, '3-specialist')
})
