"""Customer-facing wording in English (the base language), Spanish, and Portuguese. Templates fill in only
verified facts; the LLM phrasing step (app.llm.phrase) may rewrite them, and its output is checked against the
same facts. Every key has all three languages, with the same placeholders (specs/004, research R2)."""
from __future__ import annotations

from datetime import datetime

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
}


def money(amount: float, currency: str, lang: str = "es") -> str:
    """1,234.56 USD in English; 1.234,56 USD in Spanish and Portuguese (research R5). Same value everywhere."""
    if lang == "en":
        return f"{amount:,.2f} {currency}"
    s = f"{amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{s} {currency}"


def when(dt: datetime, lang: str) -> str:
    if lang == "en":
        return f"{MONTHS['en'][dt.month - 1]} {dt.day}, {dt.year}, {dt:%H:%M}"
    return f"{dt.day} de {MONTHS[lang][dt.month - 1]} de {dt.year}, {dt:%H:%M}"


def day(dt: datetime, lang: str) -> str:
    if lang == "en":
        return f"{MONTHS['en'][dt.month - 1]} {dt.day}, {dt.year}"
    return f"{dt.day} de {MONTHS[lang][dt.month - 1]} de {dt.year}"


T = {
    "greeting": {
        "en": "Hello {name}. I can help with a charge you don't recognize or think is wrong, and check whether a message or call \"from the bank\" is real. Which charge do you want to review? If you can, tell me the amount, the merchant, or the date.",
        "es": "Hola {name}. Puedo ayudarle con un cargo que no reconoce o que cree que está mal, y a revisar si un mensaje o llamada \"del banco\" es real. ¿Qué cargo quiere revisar? Si puede, dígame el monto, el comercio o la fecha.",
        "pt": "Olá, {name}. Posso ajudar com uma cobrança que você não reconhece ou acha que está errada, e verificar se uma mensagem ou ligação \"do banco\" é verdadeira. Qual cobrança você quer revisar? Se puder, diga o valor, a loja ou a data."},
    "need_details": {
        "en": "To find the charge I need at least one more detail: the amount, the merchant, or the approximate day.",
        "es": "Para encontrar el cargo necesito al menos un dato más: el monto, el comercio o el día aproximado.",
        "pt": "Para encontrar a cobrança preciso de pelo menos mais um dado: o valor, a loja ou o dia aproximado."},
    "none_found": {
        "en": "I didn't find a matching charge in the last 90 days. Can you confirm the exact amount or the day?",
        "es": "No encontré un cargo que coincida en los últimos 90 días. ¿Puede confirmar el monto exacto o el día?",
        "pt": "Não encontrei uma cobrança correspondente nos últimos 90 dias. Pode confirmar o valor exato ou o dia?"},
    "choose": {
        "en": "I found several charges that could be it. Which one is it? Reply with the number.",
        "es": "Encontré varios cargos que podrían ser. ¿Cuál es? Responda con el número.",
        "pt": "Encontrei várias cobranças que podem ser. Qual é? Responda com o número."},
    "too_many": {
        "en": "More charges match than I can show. Can you give me another detail (amount, merchant, or day) to narrow it down?",
        "es": "Hay más cargos que coinciden de los que puedo mostrar. ¿Me da otro dato (monto, comercio o día) para acotar?",
        "pt": "Há mais cobranças correspondentes do que consigo mostrar. Pode me dar outro dado (valor, loja ou dia) para restringir?"},
    "tx_core": {
        "en": "The charge is for {amount} at {merchant}, on {when}, in {city} ({country}), through the {channel} channel, with your {product} ending in {last4}.",
        "es": "El cargo es de {amount} en {merchant}, el {when}, en {city} ({country}), por el canal {channel}, con su {product} terminada en {last4}.",
        "pt": "A cobrança é de {amount} em {merchant}, em {when}, em {city} ({country}), pelo canal {channel}, com seu {product} final {last4}."},
    "tx_core_nomerchant": {
        "en": "The transaction is a {kind} of {amount}, on {when}, through the {channel} channel, on your {product} ending in {last4}.",
        "es": "El movimiento es un {kind} de {amount}, el {when}, por el canal {channel}, en su {product} terminada en {last4}.",
        "pt": "A movimentação é um(a) {kind} de {amount}, em {when}, pelo canal {channel}, no seu {product} final {last4}."},
    "pending": {
        "en": "This charge is still pending: it hasn't been applied yet. Holds from hotels, gas stations, or car rentals are usually released on their own within a few days. I don't have the exact release date.",
        "es": "Este cargo todavía está pendiente: aún no se ha aplicado. Las retenciones de hoteles, gasolineras o alquiler de autos suelen liberarse solas en unos días. No tengo la fecha exacta de liberación.",
        "pt": "Esta cobrança ainda está pendente: ainda não foi efetivada. Retenções de hotéis, postos ou aluguel de carros costumam ser liberadas sozinhas em alguns dias. Não tenho a data exata de liberação."},
    "history_yes": {
        "en": "You have paid at {merchant} {n} times before; the last one on {last}.",
        "es": "Ha pagado en {merchant} {n} veces antes; la última el {last}.",
        "pt": "Você já pagou em {merchant} {n} vezes antes; a última em {last}."},
    "history_no": {
        "en": "You have no earlier payments at {merchant}.",
        "es": "No tiene pagos anteriores en {merchant}.",
        "pt": "Você não tem pagamentos anteriores em {merchant}."},
    "risk": {
        "en": "This charge has features often seen in fraud. It is an estimate, not a conclusion.",
        "es": "Este cargo tiene rasgos que suelen verse en fraudes. Es una estimación, no una conclusión.",
        "pt": "Esta cobrança tem características comuns em fraudes. É uma estimativa, não uma conclusão."},
    "ask_confirm": {
        "en": "Do you recognize this charge now? Reply \"yes, it was me\" or \"it wasn't me\" to open a claim.",
        "es": "¿Reconoce ahora este cargo? Responda \"sí, fui yo\" o \"no fui yo\" para abrir un reclamo.",
        "pt": "Você reconhece esta cobrança agora? Responda \"sim, fui eu\" ou \"não fui eu\" para abrir uma reclamação."},
    "closed_mine": {
        "en": "Great, I've recorded it as recognized. No claim was opened. If you want to cancel a recurring charge you no longer want, you can ask the bank.",
        "es": "Perfecto, lo dejo registrado como reconocido. No se abrió ningún reclamo. Si quiere cancelar un cargo recurrente que ya no desea, puede pedirlo al banco.",
        "pt": "Perfeito, deixo registrado como reconhecido. Nenhuma reclamação foi aberta. Se quiser cancelar uma cobrança recorrente que não deseja mais, pode pedir ao banco."},
    "ask_statement": {
        "en": "I'll prepare your claim for a specialist. Tell me in your own words what happened: do you have the card with you? Did you share any code or click a link? Did you file a police report?",
        "es": "Voy a preparar su reclamo para un especialista. Cuénteme en sus palabras qué pasó: ¿tiene la tarjeta con usted? ¿Compartió algún código o hizo clic en un enlace? ¿Hizo una denuncia?",
        "pt": "Vou preparar sua reclamação para um especialista. Conte com suas palavras o que aconteceu: você está com o cartão? Compartilhou algum código ou clicou em um link? Fez boletim de ocorrência?"},
    "handoff_done": {
        "en": "Done. A specialist received your case with all the verified details (case {case}). I can't promise the outcome of the claim, but here are your rights and the deadlines:",
        "es": "Listo. Un especialista recibió su caso con todos los datos verificados (folio {case}). No puedo prometerle el resultado del reclamo; sí le digo sus derechos y los plazos:",
        "pt": "Pronto. Um especialista recebeu seu caso com todos os dados verificados (protocolo {case}). Não posso prometer o resultado da reclamação; mas informo seus direitos e prazos:"},
    "freeze_hint": {
        "en": "If you think your card is compromised, freeze it in the app. We will never ask you for codes, PINs, or passwords.",
        "es": "Si cree que su tarjeta está comprometida, congélela desde la app. Nunca le pediremos códigos, NIP ni contraseñas.",
        "pt": "Se achar que seu cartão está comprometido, bloqueie-o pelo app. Nunca pediremos códigos, PIN ou senhas."},
    "verdict_scam_asks_secret": {
        "en": "That is a scam: the bank never asks for codes, PINs, or passwords, on any channel. Don't share anything and don't reply to that contact.",
        "es": "Eso es una estafa: el banco nunca pide códigos, NIP, claves ni contraseñas, por ningún canal. No comparta nada y no responda a ese contacto.",
        "pt": "Isso é um golpe: o banco nunca pede códigos, PIN ou senhas, por nenhum canal. Não compartilhe nada e não responda a esse contato."},
    "verdict_bank_contact": {
        "en": "Yes, we have a record of the bank contacting you by {channel} on {day}. Even so, we will never ask you for codes or passwords.",
        "es": "Sí, tenemos registrado un contacto del banco con usted por {channel} el {day}. Aun así, nunca le pediremos códigos ni contraseñas.",
        "pt": "Sim, temos registrado um contato do banco com você por {channel} em {day}. Mesmo assim, nunca pediremos códigos ou senhas."},
    "verdict_no_record": {
        "en": "We have no record of the bank contacting you by {channel} on those dates. Treat it as a possible scam: don't reply or share any data, and use only the bank's official channels.",
        "es": "No tenemos registro de que el banco le haya contactado por {channel} en esas fechas. Trátelo como posible estafa: no responda ni comparta datos, y comuníquese solo por los canales oficiales.",
        "pt": "Não temos registro de que o banco tenha contatado você por {channel} nessas datas. Trate como possível golpe: não responda nem compartilhe dados, e fale apenas pelos canais oficiais."},
    "verdict_escalated": {
        "en": "Because you shared information with that contact, I passed your case to a fraud specialist (case {case}), who will contact you through the official channels. Freeze your card in the app now.",
        "es": "Como compartió información con ese contacto, pasé su caso a un especialista de fraude (folio {case}), que le contactará por los canales oficiales. Congele su tarjeta desde la app ahora.",
        "pt": "Como você compartilhou informações com esse contato, passei seu caso para um especialista em fraude (protocolo {case}), que entrará em contato pelos canais oficiais. Bloqueie seu cartão pelo app agora."},
    "ask_shared": {
        "en": "Did you share any code, password, or card details with that contact?",
        "es": "¿Llegó a compartir algún código, clave o dato de su tarjeta con ese contacto?",
        "pt": "Você chegou a compartilhar algum código, senha ou dado do cartão com esse contato?"},
    "out_of_scope": {
        "en": "I can't help with that here: I only review charges you don't recognize or think are wrong, and check contacts \"from the bank\". For other topics, please use the bank's official channels.",
        "es": "Con eso no puedo ayudarle aquí: solo reviso cargos que no reconoce o cree incorrectos, y verifico contactos \"del banco\". Para otros temas use los canales oficiales del banco.",
        "pt": "Com isso não posso ajudar aqui: só reviso cobranças que você não reconhece ou acha erradas, e verifico contatos \"do banco\". Para outros assuntos, use os canais oficiais do banco."},
    "unauthorized": {
        "en": "I can only look up information from your own account. I can't check other people's data.",
        "es": "Solo puedo consultar información de su propia cuenta. No puedo revisar datos de otras personas.",
        "pt": "Só posso consultar informações da sua própria conta. Não posso verificar dados de outras pessoas."},
    "session_expired": {
        "en": "Your session expired for your security. Sign in again to continue.",
        "es": "Su sesión expiró por seguridad. Vuelva a iniciar sesión para continuar.",
        "pt": "Sua sessão expirou por segurança. Faça login novamente para continuar."},
    "compliance_neutral": {
        "en": "For this charge I need a specialist to help you; they will contact you through the bank's official channels (case {case}). I can't give more details about it here. If you want to check another charge, I'm happy to help.",
        "es": "Para este cargo necesito que lo atienda un especialista, que le contactará por los canales oficiales del banco (folio {case}). Por este medio no puedo darle más detalles sobre él. Si quiere revisar otro cargo, con gusto le ayudo.",
        "pt": "Para esta cobrança preciso que um especialista atenda você; ele entrará em contato pelos canais oficiais do banco (protocolo {case}). Por aqui não consigo dar mais detalhes sobre ela. Se quiser revisar outra cobrança, fico à disposição."},
    "turn_limit": {
        "en": "This conversation reached its limit. Start a new session to check another charge.",
        "es": "Esta conversación llegó a su límite. Inicie una nueva sesión para revisar otro cargo.",
        "pt": "Esta conversa chegou ao limite. Inicie uma nova sessão para revisar outra cobrança."},
    "fallback": {
        "en": "I had a technical problem looking up your data. To avoid giving you wrong information, I passed your question to a person (case {case}).",
        "es": "Tuve un problema técnico al consultar sus datos. Para no darle información incorrecta, pasé su consulta a una persona (folio {case}).",
        "pt": "Tive um problema técnico ao consultar seus dados. Para não dar informação incorreta, passei sua consulta para uma pessoa (protocolo {case})."},
    "closed": {
        "en": "This case is already closed. If you want to check another charge, tell me the amount, the merchant, or the date.",
        "es": "Este caso ya está cerrado. Si quiere revisar otro cargo, dígame el monto, el comercio o la fecha.",
        "pt": "Este caso já está encerrado. Se quiser revisar outra cobrança, diga o valor, a loja ou a data."},
}

CHANNEL_NAMES = {
    "en": {"sms": "SMS", "whatsapp": "WhatsApp", "email": "email", "push": "app notification", "call": "phone call", "any": "any channel",
           "SMS": "SMS", "WhatsApp": "WhatsApp", "Email": "email", "Push": "app notification", "Voice": "phone call",
           "App": "app", "Web": "web", "POS": "in-store card terminal", "ATM": "ATM", "Branch": "branch", "Transfer": "transfer"},
    "es": {"sms": "SMS", "whatsapp": "WhatsApp", "email": "correo", "push": "notificación de la app", "call": "llamada", "any": "ningún canal",
           "SMS": "SMS", "WhatsApp": "WhatsApp", "Email": "correo", "Push": "notificación de la app", "Voice": "llamada",
           "App": "app", "Web": "web", "POS": "terminal en comercio", "ATM": "cajero", "Branch": "sucursal", "Transfer": "transferencia"},
    "pt": {"sms": "SMS", "whatsapp": "WhatsApp", "email": "e-mail", "push": "notificação do app", "call": "ligação", "any": "nenhum canal",
           "SMS": "SMS", "WhatsApp": "WhatsApp", "Email": "e-mail", "Push": "notificação do app", "Voice": "ligação",
           "App": "app", "Web": "web", "POS": "maquininha na loja", "ATM": "caixa eletrônico", "Branch": "agência", "Transfer": "transferência"},
}
PRODUCT_NAMES = {
    "en": {"Tarjeta Crédito": "credit card", "Tarjeta Débito": "debit card", "Cuenta Ahorro": "savings account",
           "Cuenta Corriente": "checking account", "Préstamo Personal": "personal loan", "Préstamo Hipotecario": "mortgage",
           "Inversión": "investment", "Seguro": "insurance"},
    "es": {"Tarjeta Crédito": "tarjeta de crédito", "Tarjeta Débito": "tarjeta de débito", "Cuenta Ahorro": "cuenta de ahorro",
           "Cuenta Corriente": "cuenta corriente", "Préstamo Personal": "préstamo personal", "Préstamo Hipotecario": "hipoteca",
           "Inversión": "inversión", "Seguro": "seguro"},
    "pt": {"Tarjeta Crédito": "cartão de crédito", "Tarjeta Débito": "cartão de débito", "Cuenta Ahorro": "conta poupança",
           "Cuenta Corriente": "conta corrente", "Préstamo Personal": "empréstimo pessoal", "Préstamo Hipotecario": "financiamento imobiliário",
           "Inversión": "investimento", "Seguro": "seguro"},
}
TX_KINDS = {
    "en": {"Payment": "payment", "Withdrawal": "withdrawal", "Transfer": "transfer", "Adjustment": "adjustment", "Purchase": "purchase"},
    "es": {"Payment": "pago", "Withdrawal": "retiro", "Transfer": "transferencia", "Adjustment": "ajuste", "Purchase": "compra"},
    "pt": {"Payment": "pagamento", "Withdrawal": "saque", "Transfer": "transferência", "Adjustment": "ajuste", "Purchase": "compra"},
}


def t(key: str, lang: str, **kw) -> str:
    return T[key][lang].format(**kw)


# Quick replies offered after each question the assistant asks, by conversation stage and language.
# Each one is understood by the rules as well as by the model (checked in tests/test_workflow.py).
QUICK_REPLIES = {
    "confirm": {"en": ["Yes, it was me", "It wasn't me"], "es": ["Sí, fui yo", "No fui yo"], "pt": ["Sim, fui eu", "Não fui eu"]},
    "statement": {"en": ["I have my card and didn't share any code", "I shared a code over the phone", "I lost my card"],
                  "es": ["Tengo la tarjeta y no compartí ningún código", "Compartí un código por teléfono", "Perdí la tarjeta"],
                  "pt": ["Estou com o cartão e não compartilhei nenhum código", "Compartilhei um código por telefone", "Perdi o cartão"]},
    "contact_shared": {"en": ["Yes, I shared it", "No, I didn't share anything"], "es": ["Sí, lo compartí", "No, no compartí nada"], "pt": ["Sim, compartilhei", "Não, não compartilhei nada"]},
}

