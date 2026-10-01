import type { Basis, ChatEvent, Handoff, Lang, ScenarioId, Verification } from './api'

// Fixed texts of every screen, one complete set per language: English (the base language), Spanish, and
// Portuguese (specs/004, FR-408; replaces specs/003 FR-201 to FR-203). Typing TEXT as Record<Lang, TextSet>
// makes a text missing in any language fail the type-check. Keep the keys in the same order in every set: the
// UI checks compare the sets position by position.

type Verdict = Extract<ChatEvent, { type: 'verdict' }>['verdict']
type Priority = Handoff['priority']
type CaseType = 'unrecognized_charge' | 'fraud_suspected' | 'fake_contact_secret_shared' | 'compliance_review' | 'technical_fallback'

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
  /** The line under the opening message: which languages the customer can write in. */
  languages: string
  app: {
    brand: string
    nav: string
    customerTab: string
    specialistTab: string
    dataAsOf: (date: string) => string
    claudeOn: string
    rulesMode: string
    connecting: string
    footer: string
  }
  signIn: {
    heading: string
    lead: string
    notice: string
    loading: string
    connectError: string
    retry: string
    list: string
    start: string
    opening: string
    limit: string
    failed: string
  }
  scenario: Record<ScenarioId, string>
  specialist: {
    title: string
    count: (n: number) => string
    loading: string
    empty: string
    goToCustomer: string
    priority: Record<Priority, string>
    caseType: Record<CaseType, string>
    field: {
      customer: string
      request: string
      statement: string
      facts: string
      product: string
      shared: string
      actions: string
      legal: string
      answerBy: string
      open: string
      security: string
    }
    shared: { yes: string; no: string; unknown: string }
    noFlags: string
    verify: {
      title: string
      hint: string
      drop: string
      or: string
      choose: string
      checking: string
      input: string
      code: string
      registry: string
      registered: string
      notRegistered: string
      cases: string
    }
    result: Record<Verification['result'], { label: string; text?: string }>
  }
}

export const TEXT: Record<Lang, TextSet> = {
  en: {
    basis: { known: 'VERIFIED', guessed: 'ESTIMATE', rule: 'RULE' },
    basisTerm: { known: 'Verified', guessed: 'Estimate', rule: 'Rule' },
    basisExplain: {
      known: 'Comes from a bank record. The reference is that record.',
      guessed: 'We inferred it from your transactions; it may not be exact.',
      rule: 'It is a bank or legal rule. The reference identifies the rule.',
    },
    sources: { title: 'Sources', toggle: 'Where does this come from?' },
    verdict: {
      bank_contact: 'A real contact from the bank',
      no_record: 'No record from the bank',
      scam_asks_secret: 'Scam: they asked you for a code',
    },
    candidate: { group: 'Charges found', pick: 'Select this one', picked: 'Selected', pending: 'Pending' },
    case: {
      kicker: 'Your case',
      label: (id) => `Case ${id}`,
      sent: (id) => `Case ${id} sent to a specialist`,
      status: 'Case status',
      received: 'Received',
      review: 'Review by a specialist',
      reviewNote: 'Next step',
      answer: 'Answer',
      answerNote: 'Within the stated period',
      keep: 'Keep your case number:',
      pdfHint: 'You can download a copy of this conversation above.',
    },
    intro: (name) => `Hello, ${name}. Tell me which charge you don't recognize, or which contact from the bank you want to check, and we'll review it together with your records.`,
    composer: { label: 'Message', placeholder: 'Write in Spanish or Portuguese…', send: 'Send' },
    typing: 'Checking your records…',
    security: 'Secure conversation · We will never ask for passwords, PINs, or SMS codes',
    assistant: 'Assistant',
    pdf: {
      button: 'Download conversation (PDF)',
      saved: 'Downloaded · check code',
      expired: 'Session expired; sign in again',
      failed: 'The PDF could not be created',
      notYet: 'Available after your first question',
    },
    steps: {
      title: 'How we review your case',
      subtitle: 'How the assistant works, step by step.',
      names: ['Understand', 'Decide', 'Act', 'Verify', 'Escalate'],
      lines: [
        'We read your message to know what you need.',
        'We choose which records to check.',
        'We look up your transactions and the bank\'s contacts.',
        'Every fact we show you comes from a record.',
        'If needed, a specialist takes your case.',
      ],
      done: 'Done',
      now: 'Now',
      progress: (n, name) => `Step ${n} of 5 · ${name}`,
      notStarted: 'Starts with your first message',
      technical: 'Technical detail (demo)',
    },
    session: {
      expiredTitle: 'Your session ended',
      expiredBody: 'For your security we closed it after a while without activity. To continue, choose your customer again.',
      restart: 'Sign in again',
      change: 'Change customer',
    },
    aria: { messages: 'Conversation', replies: 'Quick replies', examples: 'Examples', customer: 'Customer' },
    networkError: (detail) => `The service could not be reached (${detail}).`,
    languages: 'The assistant answers in Spanish or Portuguese: write in either one.',
    app: {
      brand: 'Explain this charge',
      nav: 'View',
      customerTab: 'Customer',
      specialistTab: 'Specialist',
      dataAsOf: (date) => `Data as of ${date}`,
      claudeOn: 'Claude on',
      rulesMode: 'Rules mode (no AI)',
      connecting: 'Connecting…',
      footer: 'Demo with synthetic data · Factored AI & Data Hackathon 2026',
    },
    signIn: {
      heading: "Let's review your charge together",
      lead: "Choose a customer to start. We'll explain the charge using the bank's records.",
      notice: "Synthetic test customers. In production, identity comes from the bank's sign-in.",
      loading: 'Loading test customers…',
      connectError: "We couldn't connect. Your data is safe; please try again.",
      retry: 'Try again',
      list: 'Test customers',
      start: 'Start',
      opening: 'Opening…',
      limit: 'Too many conversations were opened from this connection. Please try again later.',
      failed: "We couldn't open the conversation. Your data is safe; please try again.",
    },
    scenario: {
      fraud_flagged: 'Charge flagged by the fraud-risk estimate',
      pending: 'Pending charge',
      mx_debit_48h: 'Mexico, debit card, last 48 hours',
      co_purchase: 'Colombia, card purchase',
      ar_purchase: 'Argentina, card purchase',
      compliance: 'Charge under compliance review (synthetic)',
      bank_message: 'Received a real message from the bank',
    },
    specialist: {
      title: 'Cases to review',
      count: (n) => `${n} ${n === 1 ? 'case' : 'cases'} · sorted by priority. Each case carries only verified facts, not the whole conversation.`,
      loading: 'Loading…',
      empty: 'No cases yet. Open a claim from the chat.',
      goToCustomer: 'Go to the Customer view',
      priority: { urgent: 'Urgent', high: 'High', normal: 'Normal' },
      caseType: {
        unrecognized_charge: 'Unrecognized charge',
        fraud_suspected: 'Possible fraud',
        fake_contact_secret_shared: 'Possible scam: shared a code',
        compliance_review: 'Compliance review',
        technical_fallback: 'Technical failure',
      },
      field: {
        customer: 'Customer',
        request: 'Request',
        statement: "Customer's account",
        facts: 'Verified facts',
        product: 'Product',
        shared: 'Shared a code?',
        actions: 'Actions',
        legal: 'Legal framework',
        answerBy: 'answer by',
        open: 'Open questions',
        security: 'Security',
      },
      shared: { yes: 'Yes', no: 'No', unknown: 'Not stated' },
      noFlags: 'No alerts',
      verify: {
        title: 'Verify a conversation PDF',
        hint: 'Only the original file matches. A copy that was edited or saved again shows as altered.',
        drop: "Drop the customer's PDF here",
        or: 'or',
        choose: 'Choose file',
        checking: 'Checking…',
        input: "Choose the customer's PDF",
        code: 'Code',
        registry: 'Register',
        registered: 'Registered',
        notRegistered: 'Not in the current register',
        cases: 'Cases',
      },
      result: {
        match: { label: 'Match' },
        altered: { label: 'Altered', text: 'This file changed after it was downloaded. Ask the customer for the original PDF.' },
        unknown_version: { label: 'Unknown version', text: 'The PDF uses a format we do not recognize. It may come from another version of the app.' },
        unreadable: { label: 'Unreadable', text: "We couldn't read this file. Try the original PDF." },
      },
    },
  },
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
    languages: 'Puede escribir en español o en portugués · Pode escrever em espanhol ou em português',
    app: {
      brand: 'Explica este cargo',
      nav: 'Vista',
      customerTab: 'Cliente',
      specialistTab: 'Especialista',
      dataAsOf: (date) => `Datos al ${date}`,
      claudeOn: 'Claude activo',
      rulesMode: 'Modo reglas (sin IA)',
      connecting: 'Conectando…',
      footer: 'Demostración con datos sintéticos · Factored AI & Data Hackathon 2026',
    },
    signIn: {
      heading: 'Revisemos juntos su cargo',
      lead: 'Elija un cliente para empezar. Le explicaremos el cargo con los registros del banco.',
      notice: 'Clientes sintéticos de prueba. En producción la identidad viene del inicio de sesión del banco.',
      loading: 'Cargando clientes de prueba…',
      connectError: 'No pudimos conectar. Sus datos están a salvo; intente de nuevo.',
      retry: 'Reintentar',
      list: 'Clientes de prueba',
      start: 'Empezar',
      opening: 'Abriendo…',
      limit: 'Se abrieron demasiadas conversaciones desde esta conexión. Intente de nuevo más tarde.',
      failed: 'No pudimos abrir la conversación. Sus datos están a salvo; intente de nuevo.',
    },
    scenario: {
      fraud_flagged: 'Cargo marcado por el estimador de riesgo de fraude',
      pending: 'Cargo pendiente',
      mx_debit_48h: 'México, tarjeta de débito, últimas 48 horas',
      co_purchase: 'Colombia, compra con tarjeta',
      ar_purchase: 'Argentina, compra con tarjeta',
      compliance: 'Cargo en revisión de cumplimiento (sintético)',
      bank_message: 'Recibió un mensaje real del banco',
    },
    specialist: {
      title: 'Casos para revisar',
      count: (n) => `${n} ${n === 1 ? 'caso' : 'casos'} · ordenados por prioridad. Cada caso trae solo hechos verificados, no la conversación completa.`,
      loading: 'Cargando…',
      empty: 'Sin casos todavía. Abra un reclamo desde el chat.',
      goToCustomer: 'Ir a la vista Cliente',
      priority: { urgent: 'Urgente', high: 'Alta', normal: 'Normal' },
      caseType: {
        unrecognized_charge: 'Cargo no reconocido',
        fraud_suspected: 'Posible fraude',
        fake_contact_secret_shared: 'Posible estafa: compartió un código',
        compliance_review: 'Revisión de cumplimiento',
        technical_fallback: 'Falla técnica',
      },
      field: {
        customer: 'Cliente',
        request: 'Solicitud',
        statement: 'Relato del cliente',
        facts: 'Hechos verificados',
        product: 'Producto',
        shared: '¿Compartió código?',
        actions: 'Acciones',
        legal: 'Marco legal',
        answerBy: 'responder antes de',
        open: 'Preguntas abiertas',
        security: 'Seguridad',
      },
      shared: { yes: 'Sí', no: 'No', unknown: 'No indicado' },
      noFlags: 'Sin alertas',
      verify: {
        title: 'Verificar PDF de conversación',
        hint: 'Solo el archivo original coincide. Una copia editada o guardada de nuevo aparece como alterada.',
        drop: 'Arrastre aquí el PDF del cliente',
        or: 'o',
        choose: 'Elegir archivo',
        checking: 'Verificando…',
        input: 'Elegir el PDF del cliente',
        code: 'Código',
        registry: 'Registro',
        registered: 'Registrado',
        notRegistered: 'No está en el registro actual',
        cases: 'Casos',
      },
      result: {
        match: { label: 'Coincide' },
        altered: { label: 'Alterado', text: 'Este archivo cambió después de descargarse. Pida al cliente el PDF original.' },
        unknown_version: { label: 'Versión desconocida', text: 'El PDF usa un formato que no reconocemos. Puede ser de otra versión de la app.' },
        unreadable: { label: 'No legible', text: 'No pudimos leer este archivo. Pruebe con el PDF original.' },
      },
    },
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
    languages: 'Puede escribir en español o en portugués · Pode escrever em espanhol ou em português',
    app: {
      brand: 'Explique esta cobrança',
      nav: 'Visualização',
      customerTab: 'Cliente',
      specialistTab: 'Especialista',
      dataAsOf: (date) => `Dados de ${date}`,
      claudeOn: 'Claude ativo',
      rulesMode: 'Modo regras (sem IA)',
      connecting: 'Conectando…',
      footer: 'Demonstração com dados sintéticos · Factored AI & Data Hackathon 2026',
    },
    signIn: {
      heading: 'Vamos revisar juntos a sua cobrança',
      lead: 'Escolha um cliente para começar. Explicaremos a cobrança com os registros do banco.',
      notice: 'Clientes sintéticos de teste. Em produção, a identidade vem do login do banco.',
      loading: 'Carregando clientes de teste…',
      connectError: 'Não conseguimos conectar. Seus dados estão seguros; tente novamente.',
      retry: 'Tentar novamente',
      list: 'Clientes de teste',
      start: 'Começar',
      opening: 'Abrindo…',
      limit: 'Foram abertas conversas demais a partir desta conexão. Tente novamente mais tarde.',
      failed: 'Não conseguimos abrir a conversa. Seus dados estão seguros; tente novamente.',
    },
    scenario: {
      fraud_flagged: 'Cobrança sinalizada pelo estimador de risco de fraude',
      pending: 'Cobrança pendente',
      mx_debit_48h: 'México, cartão de débito, últimas 48 horas',
      co_purchase: 'Colômbia, compra com cartão',
      ar_purchase: 'Argentina, compra com cartão',
      compliance: 'Cobrança em revisão de conformidade (sintético)',
      bank_message: 'Recebeu uma mensagem real do banco',
    },
    specialist: {
      title: 'Casos para revisar',
      count: (n) => `${n} ${n === 1 ? 'caso' : 'casos'} · ordenados por prioridade. Cada caso traz só fatos verificados, não a conversa completa.`,
      loading: 'Carregando…',
      empty: 'Nenhum caso ainda. Abra uma reclamação pelo chat.',
      goToCustomer: 'Ir para a visualização Cliente',
      priority: { urgent: 'Urgente', high: 'Alta', normal: 'Normal' },
      caseType: {
        unrecognized_charge: 'Cobrança não reconhecida',
        fraud_suspected: 'Possível fraude',
        fake_contact_secret_shared: 'Possível golpe: compartilhou um código',
        compliance_review: 'Revisão de conformidade',
        technical_fallback: 'Falha técnica',
      },
      field: {
        customer: 'Cliente',
        request: 'Solicitação',
        statement: 'Relato do cliente',
        facts: 'Fatos verificados',
        product: 'Produto',
        shared: 'Compartilhou código?',
        actions: 'Ações',
        legal: 'Marco legal',
        answerBy: 'responder até',
        open: 'Perguntas em aberto',
        security: 'Segurança',
      },
      shared: { yes: 'Sim', no: 'Não', unknown: 'Não informado' },
      noFlags: 'Sem alertas',
      verify: {
        title: 'Verificar PDF da conversa',
        hint: 'Só o arquivo original confere. Uma cópia editada ou salva novamente aparece como alterada.',
        drop: 'Arraste aqui o PDF do cliente',
        or: 'ou',
        choose: 'Escolher arquivo',
        checking: 'Verificando…',
        input: 'Escolher o PDF do cliente',
        code: 'Código',
        registry: 'Registro',
        registered: 'Registrado',
        notRegistered: 'Não está no registro atual',
        cases: 'Casos',
      },
      result: {
        match: { label: 'Confere' },
        altered: { label: 'Alterado', text: 'Este arquivo mudou depois de ser baixado. Peça ao cliente o PDF original.' },
        unknown_version: { label: 'Versão desconhecida', text: 'O PDF usa um formato que não reconhecemos. Pode ser de outra versão do app.' },
        unreadable: { label: 'Ilegível', text: 'Não conseguimos ler este arquivo. Tente com o PDF original.' },
      },
    },
  },
}

export function useText(lang: Lang): TextSet {
  return TEXT[lang]
}
