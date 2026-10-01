import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { TEXT } from '../src/i18n'
import { claimPath, noSideScroll, send } from './helpers'

// specs/004 US5: switching language re-shows the whole conversation (FR-420 to FR-423; SC-405). Rules mode: the
// assistant's messages are rebuilt from their recipes; the customer's words have no translation, so they are shown
// as written with a note.

async function sources(page: import('@playwright/test').Page) {
  return page.locator('.msg.assistant .source-ref').allInnerTexts()
}

test('the demo path: a Spanish claim, then Portuguese', async ({ page }) => {
  await claimPath(page)
  const caseId = (await page.locator('.case-card .case-id, .case-card').first().innerText()).match(/CASO-[A-Z0-9]+/)![0]
  const before = await sources(page)

  await send(page, 'Obrigado, entendi')
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt')
  await expect(page.locator('.msg.assistant').first()).toContainText('A cobrança é de')
  await expect(page.locator('.case-card')).toContainText(TEXT.pt.case.sent(caseId))
  expect((await sources(page)).slice(0, before.length)).toEqual(before)   // the same references, in order
  // The customer's Spanish words, shown as written, with the note in Portuguese.
  const first = page.locator('.msg.customer').first()
  await expect(first).toHaveAttribute('lang', 'es')
  await expect(first).toContainText(TEXT.pt.reshow.noTranslation)
  await expect(page.getByRole('status').filter({ hasText: TEXT.pt.reshow.announced })).toHaveCount(1)

  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(violations.map((v) => v.id)).toEqual([])
  await noSideScroll(page)
})
