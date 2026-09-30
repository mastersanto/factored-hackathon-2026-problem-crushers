import type { Basis, ChatEvent, Lang } from './api'

// Fixed texts of the customer's chat, one complete set per language (specs/003, R1). The chat shows the set of
// the latest assistant message's language, the same rule the transcript PDF uses (specs/002, FR-109). Typing
// TEXT as Record<Lang, TextSet> makes a text missing in either language fail the type-check (FR-201).
// Sign-in, the header, and the specialist view are used before a conversation or by bank staff, and stay in
// Spanish (FR-203).

type Verdict = Extract<ChatEvent, { type: 'verdict' }>['verdict']

export interface TextSet {
  basis: Record<Basis, string>
  basisTerm: Record<Basis, string>
  basisExplain: Record<Basis, string>
  sources: { title: string; toggle: string }
  verdict: Record<Verdict, string>
  candidate: { group: string; pick: string; picked: string; pending: string }
  case: {
    kicker: string
    label: (id: string) => string
    sent: (id: string) => string
    status: string
    received: string
    review: string
    reviewNote: string
    answer: string
    answerNote: string
    keep: string
    pdfHint: string
  }
  intro: (name: string) => string
  composer: { label: string; placeholder: string; send: string }
  typing: string
  security: string
  assistant: string
  pdf: { button: string; saved: string; expired: string; failed: string; notYet: string }
  steps: {
    title: string
    subtitle: string
    names: [string, string, string, string, string]
    lines: [string, string, string, string, string]
    done: string
    now: string
    progress: (n: number, name: string) => string
    notStarted: string
    technical: string
  }
  session: { expiredTitle: string; expiredBody: string; restart: string; change: string }
  aria: { messages: string; replies: string; examples: string; customer: string }
  networkError: (detail: string) => string
}

export const TEXT: Record<Lang, TextSet> = {
  es: {
    basis: { known: 'VERIFICADO', guessed: 'ESTIMACIÓN', rule: 'POLÍTICA' },
    basisTerm: { known: 'Verificado', guessed: 'Estimación', rule: 'Política' },
    basisExplain: {
      known: 'Viene de un registro del banco. La referencia es ese registro.',
      guessed: 'Lo deducimos de sus movimientos; puede no ser exacto.',
      rule: 'Es una regla del banco o de la ley. La referencia identifica la regla.',
    },
    sources: { title: 'Fuentes', toggle: '¿De dónde sale este dato?' },
    verdict: {
      bank_contact: 'Contacto real del banco',
      no_record: 'Sin registro del banco',
      scam_asks_secret: 'Estafa: le pidieron un código',
    },
    candidate: { group: 'Cargos encontrados', pick: 'Seleccionar este', picked: 'Seleccionado', pending: 'Pendiente' },
    case: {
      kicker: 'Su caso',
      label: (id) => `Caso ${id}`,
      sent: (id) => `Caso ${id} enviado a un especialista`,
      status: 'Estado del caso',
      received: 'Recibido',
      review: 'Revisión por un especialista',
      reviewNote: 'Siguiente paso',
      answer: 'Respuesta',
      answerNote: 'En el plazo indicado',
      keep: 'Guarde su número de caso:',
      pdfHint: 'Puede descargar una copia de esta conversación arriba.',
    },
    intro: (name) => `Hola, ${name}. Cuénteme qué cargo no reconoce, o qué contacto del banco quiere revisar, y lo revisamos juntos con sus registros.`,
    composer: { label: 'Mensaje', placeholder: 'Escriba en español o português…', send: 'Enviar' },
    typing: 'Revisando sus registros…',
    security: 'Conversación segura · Nunca le pediremos contraseñas, PIN ni códigos SMS',
    assistant: 'Asistente',
    pdf: {
      button: 'Descargar conversación (PDF)',
      saved: 'Descargado · código de verificación',
      expired: 'Sesión expirada; inicie sesión de nuevo',
      failed: 'No se pudo generar el PDF',
      notYet: 'Disponible al terminar la primera consulta',
    },
    steps: {
      title: 'Cómo revisamos su caso',
      subtitle: 'Así trabaja el asistente, paso a paso.',
      names: ['Entender', 'Decidir', 'Actuar', 'Verificar', 'Escalar'],
      lines: [
        'Leemos su mensaje para saber qué necesita.',
        'Elegimos qué registros hay que revisar.',
        'Consultamos sus movimientos y los contactos del banco.',
        'Cada dato que le mostramos sale de un registro.',
        'Si hace falta, un especialista toma su caso.',
      ],
      done: 'Listo',
      now: 'Ahora',
      progress: (n, name) => `Paso ${n} de 5 · ${name}`,
      notStarted: 'Empieza con su primer mensaje',
      technical: 'Detalle técnico (demo)',
    },
    session: {
      expiredTitle: 'Su sesión terminó',
      expiredBody: 'Por su seguridad la cerramos tras un rato sin actividad. Para seguir, vuelva a elegir su cliente.',
      restart: 'Iniciar sesión de nuevo',
      change: 'Cambiar cliente',
    },
    aria: { messages: 'Conversación', replies: 'Respuestas rápidas', examples: 'Ejemplos', customer: 'Cliente' },
    networkError: (detail) => `No se pudo contactar el servicio (${detail}).`,
  },
  pt: {
    basis: { known: 'VERIFICADO', guessed: 'ESTIMATIVA', rule: 'POLÍTICA' },
    basisTerm: { known: 'Verificado', guessed: 'Estimativa', rule: 'Política' },
    basisExplain: {
      known: 'Vem de um registro do banco. A referência é esse registro.',
      guessed: 'Deduzimos das suas movimentações; pode não ser exato.',
      rule: 'É uma regra do banco ou da lei. A referência identifica a regra.',
    },
    sources: { title: 'Fontes', toggle: 'De onde vem esta informação?' },
    verdict: {
      bank_contact: 'Contato real do banco',
      no_record: 'Sem registro do banco',
      scam_asks_secret: 'Golpe: pediram um código',
    },
    candidate: { group: 'Cobranças encontradas', pick: 'Selecionar esta', picked: 'Selecionada', pending: 'Pendente' },
    case: {
      kicker: 'Seu caso',
      label: (id) => `Caso ${id}`,
      sent: (id) => `Caso ${id} enviado a um especialista`,
      status: 'Status do caso',
      received: 'Recebido',
      review: 'Revisão por um especialista',
      reviewNote: 'Próximo passo',
      answer: 'Resposta',
      answerNote: 'No prazo informado',
      keep: 'Guarde o número do seu caso:',
      pdfHint: 'Você pode baixar uma cópia desta conversa acima.',
    },
    intro: (name) => `Olá, ${name}. Conte-me qual cobrança você não reconhece, ou qual contato do banco quer verificar, e revisamos juntos com os seus registros.`,
    composer: { label: 'Mensagem', placeholder: 'Escreva em português ou español…', send: 'Enviar' },
    typing: 'Revisando os seus registros…',
    security: 'Conversa segura · Nunca pediremos senhas, PIN nem códigos SMS',
    assistant: 'Assistente',
    pdf: {
      button: 'Baixar conversa (PDF)',
      saved: 'Baixado · código de verificação',
      expired: 'Sessão expirada; entre novamente',
      failed: 'Não foi possível gerar o PDF',
      notYet: 'Disponível após a primeira consulta',
    },
    steps: {
      title: 'Como revisamos o seu caso',
      subtitle: 'Assim trabalha o assistente, passo a passo.',
      names: ['Entender', 'Decidir', 'Agir', 'Verificar', 'Encaminhar'],
      lines: [
        'Lemos a sua mensagem para saber do que você precisa.',
        'Escolhemos quais registros revisar.',
        'Consultamos as suas movimentações e os contatos do banco.',
        'Cada dado que mostramos vem de um registro.',
        'Se necessário, um especialista assume o seu caso.',
      ],
      done: 'Pronto',
      now: 'Agora',
      progress: (n, name) => `Passo ${n} de 5 · ${name}`,
      notStarted: 'Começa com a sua primeira mensagem',
      technical: 'Detalhe técnico (demo)',
    },
    session: {
      expiredTitle: 'Sua sessão terminou',
      expiredBody: 'Por segurança, encerramos a sessão após um tempo sem atividade. Para continuar, escolha o cliente novamente.',
      restart: 'Entrar novamente',
      change: 'Trocar cliente',
    },
    aria: { messages: 'Conversa', replies: 'Respostas rápidas', examples: 'Exemplos', customer: 'Cliente' },
    networkError: (detail) => `Não foi possível contatar o serviço (${detail}).`,
  },
}

/** The opening line invites both languages before the first reply (US1, scenario 3). */
export const BOTH_LANGUAGES = 'Puede escribir en español o en portugués · Pode escrever em espanhol ou em português'

export function useText(lang: Lang): TextSet {
  return TEXT[lang]
}
