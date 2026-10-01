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
  | { type: 'done'; stage: string; suggestions: string[] | null; lang?: Lang }

export type Lang = 'es' | 'pt'

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

export class HttpError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new HttpError(res.status, `${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  health: () => fetch('/api/health').then(json<{ as_of: string; llm_enabled: boolean }>),
  demoCustomers: () => fetch('/api/demo/customers').then(json<DemoCustomer[]>),
  handoffs: () => fetch('/api/handoffs').then(json<Handoff[]>),
  startSession: (customer_id: string) =>
    fetch('/api/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ customer_id }) })
      .then(json<{ session_id: string; conversation_ref: string; customer: { first_name: string; country: string } }>),
}

/** Download the conversation as a PDF (specs/002). The server builds it from what it streamed to this
 *  session; the browser only saves the file. Returns the check code printed on it. */
export async function downloadTranscript(sessionId: string, conversationRef: string): Promise<string> {
  const res = await fetch('/api/transcript', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, conversation_ref: conversationRef }),
  })
  if (!res.ok) throw new HttpError(res.status, res.statusText)
  const name = /filename="([^"]+)"/.exec(res.headers.get('Content-Disposition') ?? '')?.[1] ?? 'conversacion.pdf'
  const url = URL.createObjectURL(await res.blob())
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return res.headers.get('X-Check-Code') ?? ''
}

export interface Verification {
  result: 'match' | 'altered' | 'unknown_version' | 'unreadable'
  check_code?: string | null
  registered?: boolean
  generated_at?: string
  case_ids?: string[]
}

export async function verifyTranscript(file: File): Promise<Verification> {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch('/api/transcripts/verify', { method: 'POST', body })
  if (res.status === 413) return { result: 'unreadable' }
  return json<Verification>(res)
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
