import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import type { Lang } from '../src/api'
import { TEXT } from '../src/i18n'
import { chargeMessage, contactMessage, noSideScroll, reply, SCAM, SCENARIO, send, signIn } from './helpers'

// specs/006: the panel shows where the inquiry stands (US1), and replies follow the message (US2). contracts/ui.md.

const steps = TEXT.es.steps

async function axe(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`)).toEqual([])
}

/** The visible panel's list: the rail on wide screens, the drawer (opened) on phones. */
async function panel(page: Page, isMobile: boolean) {
  if (isMobile) {
    const toggle = page.locator('.drawer-toggle')
    if (await toggle.getAttribute('aria-expanded') === 'false') await toggle.click()
    return page.locator('.steps-drawer')
  }
  return page.locator('.steps-rail')
}

/** The panel shows `names` with stage `n` current (or every stage done, with `outcome`). */
async function expectStage(page: Page, isMobile: boolean, names: string[], n: number | 'done', outcome?: RegExp | string) {
  const p = await panel(page, isMobile)
  const items = p.locator('ol.steps > li')
  await expect(items).toHaveCount(names.length)
  for (const [i, name] of names.entries()) await expect(items.nth(i)).toContainText(name)
  if (n === 'done') {
    await expect(p.locator('[aria-current="step"]')).toHaveCount(0)
    await expect(p.locator('ol.steps > li.done')).toHaveCount(names.length)
    await expect(p.locator('.steps-outcome')).toContainText(outcome!)
  } else {
    await expect(p.locator('[aria-current="step"]')).toHaveCount(1)
    await expect(items.nth(n - 1)).toHaveAttribute('aria-current', 'step')
    await expect(p.locator('.steps-outcome')).toHaveCount(0)
  }
}

async function summary(page: Page) {
  return page.locator('.drawer-toggle .muted')
}

test('not started: nothing current', async ({ page, isMobile }) => {
  await signIn(page, SCENARIO.claim)
  const p = await panel(page, isMobile)
  await expect(p.locator('[aria-current="step"]')).toHaveCount(0)
  await expect(p.locator('ol.steps > li.done')).toHaveCount(0)
  if (isMobile) await expect(await summary(page)).toHaveText(steps.notStarted)
  await axe(page)
})

test('the claim path moves stage by stage and ends with the case number', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await expectStage(page, isMobile, steps.charge.names, 3)
  if (isMobile) await expect(await summary(page)).toHaveText(steps.progress(3, 5, steps.charge.names[2]))
  await reply(page, 'No fui yo')
  await expectStage(page, isMobile, steps.charge.names, 4)
  await reply(page, 'Tengo la tarjeta y no compartí ningún código')
  const card = await page.locator('.case-card').innerText()
  const caseId = card.match(/CASO-[0-9A-F]{6}/)![0]
  await expectStage(page, isMobile, steps.charge.names, 'done', steps.outcomes.specialist(caseId))
  if (isMobile) {
    await expect(await summary(page)).toHaveText(steps.outcomes.specialist(caseId))
    await noSideScroll(page)
  }
  await axe(page)
})

test('a recognized charge closes as recognized', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await reply(page, 'Sí, fui yo')
  await expectStage(page, isMobile, steps.charge.names, 'done', steps.outcomes.recognized(null))
})

test('the contact path shows its own stages and the verdict', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.contact)
  await send(page, contactMessage(c, 'es'))
  await expectStage(page, isMobile, steps.contact.names, 'done', steps.outcomes.genuine(null))
  await axe(page)
})

test('a greeting at "was it you?" re-asks the question and leaves the panel (US2)', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await send(page, 'hola')
  await expectStage(page, isMobile, steps.charge.names, 3)
  await expect(page.locator('.msg.assistant').last()).toContainText(`Hola, ${c.first_name.split(' ')[0]}.`)  // specs/007
  await expect(page.locator('.msg.assistant').last()).toContainText('¿Reconoce ahora este cargo?')
  await expect(page.locator('.chips.replies').getByRole('button')).toHaveText(['Sí, fui yo', 'No fui yo'])
})

test('an unclear answer to "did you share anything?" is asked again (US2)', async ({ page, isMobile }) => {
  await signIn(page, SCENARIO.other)
  await send(page, SCAM)
  await expectStage(page, isMobile, steps.contact.names, 3)
  await send(page, 'mmm')
  await expectStage(page, isMobile, steps.contact.names, 3)
  await expect(page.locator('.msg.assistant').last()).toContainText('¿Llegó a compartir')
  await expect(page.locator('.chips.replies').getByRole('button')).toHaveCount(2)
  await axe(page)
})

test('a search reply names what was searched for and asks only for the rest (US2)', async ({ page }) => {
  await signIn(page, SCENARIO.claim)
  await send(page, 'No reconozco un cargo de 7,13')
  const last = page.locator('.msg.assistant').last()
  await expect(last).toContainText('7,13')
  await expect(last).toContainText('el comercio o el día')
})

test('switching language keeps the stage', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await reply(page, 'No fui yo')
  await page.getByRole('button', { name: 'Português' }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt')
  await expectStage(page, isMobile, TEXT.pt.steps.charge.names, 4)
})

test('a new inquiry after a closed one starts again', async ({ page, isMobile }) => {
  const c = await signIn(page, SCENARIO.claim)
  await send(page, chargeMessage(c))
  await reply(page, 'Sí, fui yo')
  await expectStage(page, isMobile, steps.charge.names, 'done', steps.outcomes.recognized(null))
  await send(page, chargeMessage(c))
  await expectStage(page, isMobile, steps.charge.names, 3)
})

for (const lang of ['en', 'pt'] as Lang[]) {
  test.describe(`in ${lang}`, () => {
    test.use({ locale: lang === 'en' ? 'en-US' : 'pt-BR' })
    test('the panel uses the language\'s stage names', async ({ page, isMobile }) => {
      const c = await signIn(page, SCENARIO.claim, lang)
      const before = await page.locator('.msg.assistant .msg-time').count()
      await page.locator('.chips:not(.replies)').getByRole('button').first().click()
      await expect(page.locator('.msg.assistant .msg-time')).toHaveCount(before + 1, { timeout: 30_000 })
      await expectStage(page, isMobile, TEXT[lang].steps.charge.names, 3)
      expect(c.examples[lang].length).toBeGreaterThan(0)
    })
  })
}
