// Types and calls for the local API. Chat replies stream as server-sent events over a POST.

export type Basis = 'known' | 'guessed' | 'rule'
export interface Statement { text: string; basis: Basis; source: string | null }

export type ChatEvent =
  | { type: 'step'; step: 'understand' | 'decide' | 'act' | 'verify' | 'escalate'; [k: string]: unknown }
  | { type: 'message'; text: string; statements: Statement[] }
  | { type: 'candidates'; items: Candidate[] }
  | { type: 'verdict'; verdict: 'scam_asks_secret' | 'bank_contact' | 'no_record'; channel: string }
  | { type: 'handoff'; handoff: { case_id: string } }  // the customer sees only the case number
  | { type: 'error'; code: string; text: string }
  | { type: 'done'; stage: string; suggestions: string[] | null }

export interface Candidate { option: number; transaction_id: string; when: string; amount: string; merchant: string; status: string }

export interface Handoff {
  case_id: string
  created_at: string
  case_type: string
  priority: 'normal' | 'high' | 'urgent'
  language: string
  customer: { customer_id: string; first_name: string; country: string; segment: string }
  request: string
  verified_facts: Record<string, string | number | null> | null
  actions_taken: string[]
  customer_statement?: string
  shared_secret?: boolean | null
  card?: Record<string, string | boolean | number | null>
  rights?: string[]
  answer_by?: string
  open_questions?: string[]
  security_flags: string[]
}

export interface DemoCustomer {
  label: string
  customer_id: string
  first_name: string
  country: string
  hint: Record<string, string | number | null>
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  health: () => fetch('/api/health').then(json<{ as_of: string; llm_enabled: boolean }>),
  demoCustomers: () => fetch('/api/demo/customers').then(json<DemoCustomer[]>),
  handoffs: () => fetch('/api/handoffs').then(json<Handoff[]>),
  startSession: (customer_id: string) =>
    fetch('/api/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ customer_id }) })
      .then(json<{ session_id: string; customer: { first_name: string; country: string } }>),
}

/** POST a chat turn and call onEvent for each server-sent event as it arrives. */
export async function streamChat(sessionId: string, text: string, onEvent: (e: ChatEvent) => void): Promise<void> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, text }),
  })
  if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`)
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += value
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      const data = frame.split('\n').filter((l) => l.startsWith('data: ')).map((l) => l.slice(6)).join('\n')
      if (data) onEvent(JSON.parse(data) as ChatEvent)
    }
  }
}
