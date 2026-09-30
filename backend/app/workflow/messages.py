"""Customer-facing wording in Spanish and Portuguese. Templates fill in only verified facts; the
LLM phrasing step (app.llm.phrase) may rewrite them, and its output is checked against the same facts."""
from __future__ import annotations

from datetime import datetime

MONTHS = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
}


def money(amount: float, currency: str) -> str:
    s = f"{amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{s} {currency}"


def when(dt: datetime, lang: str) -> str:
    return f"{dt.day} de {MONTHS[lang][dt.month - 1]} de {dt.year}, {dt:%H:%M}"


def day(dt: datetime, lang: str) -> str:
    return f"{dt.day} de {MONTHS[lang][dt.month - 1]} de {dt.year}"


T = {
    "greeting": {
        "es": "Hola {name}. Puedo ayudarle con un cargo que no reconoce o que cree que está mal, y a revisar si un mensaje o llamada \"del banco\" es real. ¿Qué cargo quiere revisar? Si puede, dígame el monto, el comercio o la fecha.",
        "pt": "Olá, {name}. Posso ajudar com uma cobrança que você não reconhece ou acha que está errada, e verificar se uma mensagem ou ligação \"do banco\" é verdadeira. Qual cobrança você quer revisar? Se puder, diga o valor, a loja ou a data."},
    "need_details": {
        "es": "Para encontrar el cargo necesito al menos un dato más: el monto, el comercio o el día aproximado.",
        "pt": "Para encontrar a cobrança preciso de pelo menos mais um dado: o valor, a loja ou o dia aproximado."},
    "none_found": {
        "es": "No encontré un cargo que coincida en los últimos 90 días. ¿Puede confirmar el monto exacto o el día?",
        "pt": "Não encontrei uma cobrança correspondente nos últimos 90 dias. Pode confirmar o valor exato ou o dia?"},
    "choose": {
        "es": "Encontré varios cargos que podrían ser. ¿Cuál es? Responda con el número.",
        "pt": "Encontrei várias cobranças que podem ser. Qual é? Responda com o número."},
    "too_many": {
        "es": "Hay más cargos que coinciden de los que puedo mostrar. ¿Me da otro dato (monto, comercio o día) para acotar?",
        "pt": "Há mais cobranças correspondentes do que consigo mostrar. Pode me dar outro dado (valor, loja ou dia) para restringir?"},
    "tx_core": {
        "es": "El cargo es de {amount} en {merchant}, el {when}, en {city} ({country}), por el canal {channel}, con su {product} terminada en {last4}.",
        "pt": "A cobrança é de {amount} em {merchant}, em {when}, em {city} ({country}), pelo canal {channel}, com seu {product} final {last4}."},
    "tx_core_nomerchant": {
        "es": "El movimiento es un {kind} de {amount}, el {when}, por el canal {channel}, en su {product} terminada en {last4}.",
        "pt": "A movimentação é um(a) {kind} de {amount}, em {when}, pelo canal {channel}, no seu {product} final {last4}."},
    "pending": {
        "es": "Este cargo todavía está pendiente: aún no se ha aplicado. Las retenciones de hoteles, gasolineras o alquiler de autos suelen liberarse solas en unos días. No tengo la fecha exacta de liberación.",
        "pt": "Esta cobrança ainda está pendente: ainda não foi efetivada. Retenções de hotéis, postos ou aluguel de carros costumam ser liberadas sozinhas em alguns dias. Não tenho a data exata de liberação."},
    "history_yes": {
        "es": "Ha pagado en {merchant} {n} veces antes; la última el {last}.",
        "pt": "Você já pagou em {merchant} {n} vezes antes; a última em {last}."},
    "history_no": {
        "es": "No tiene pagos anteriores en {merchant}.",
        "pt": "Você não tem pagamentos anteriores em {merchant}."},
    "risk": {
        "es": "Este cargo tiene rasgos que suelen verse en fraudes. Es una estimación, no una conclusión.",
        "pt": "Esta cobrança tem características comuns em fraudes. É uma estimativa, não uma conclusão."},
    "ask_confirm": {
        "es": "¿Reconoce ahora este cargo? Responda \"sí, fui yo\" o \"no fui yo\" para abrir un reclamo.",
        "pt": "Você reconhece esta cobrança agora? Responda \"sim, fui eu\" ou \"não fui eu\" para abrir uma reclamação."},
    "closed_mine": {
        "es": "Perfecto, lo dejo registrado como reconocido. No se abrió ningún reclamo. Si quiere cancelar un cargo recurrente que ya no desea, puede pedirlo al banco.",
        "pt": "Perfeito, deixo registrado como reconhecido. Nenhuma reclamação foi aberta. Se quiser cancelar uma cobrança recorrente que não deseja mais, pode pedir ao banco."},
    "ask_statement": {
        "es": "Voy a preparar su reclamo para un especialista. Cuénteme en sus palabras qué pasó: ¿tiene la tarjeta con usted? ¿Compartió algún código o hizo clic en un enlace? ¿Hizo una denuncia?",
        "pt": "Vou preparar sua reclamação para um especialista. Conte com suas palavras o que aconteceu: você está com o cartão? Compartilhou algum código ou clicou em um link? Fez boletim de ocorrência?"},
    "handoff_done": {
        "es": "Listo. Un especialista recibió su caso con todos los datos verificados (folio {case}). No puedo prometerle el resultado del reclamo; sí le digo sus derechos y los plazos:",
        "pt": "Pronto. Um especialista recebeu seu caso com todos os dados verificados (protocolo {case}). Não posso prometer o resultado da reclamação; mas informo seus direitos e prazos:"},
    "freeze_hint": {
        "es": "Si cree que su tarjeta está comprometida, congélela desde la app. Nunca le pediremos códigos, NIP ni contraseñas.",
        "pt": "Se achar que seu cartão está comprometido, bloqueie-o pelo app. Nunca pediremos códigos, PIN ou senhas."},
    "verdict_scam_asks_secret": {
        "es": "Eso es una estafa: el banco nunca pide códigos, NIP, claves ni contraseñas, por ningún canal. No comparta nada y no responda a ese contacto.",
        "pt": "Isso é um golpe: o banco nunca pede códigos, PIN ou senhas, por nenhum canal. Não compartilhe nada e não responda a esse contato."},
    "verdict_bank_contact": {
        "es": "Sí, tenemos registrado un contacto del banco con usted por {channel} el {day}. Aun así, nunca le pediremos códigos ni contraseñas.",
        "pt": "Sim, temos registrado um contato do banco com você por {channel} em {day}. Mesmo assim, nunca pediremos códigos ou senhas."},
    "verdict_no_record": {
        "es": "No tenemos registro de que el banco le haya contactado por {channel} en esas fechas. Trátelo como posible estafa: no responda ni comparta datos, y comuníquese solo por los canales oficiales.",
        "pt": "Não temos registro de que o banco tenha contatado você por {channel} nessas datas. Trate como possível golpe: não responda nem compartilhe dados, e fale apenas pelos canais oficiais."},
    "verdict_escalated": {
        "es": "Como compartió información con ese contacto, pasé su caso a un especialista de fraude (folio {case}), que le contactará por los canales oficiales. Congele su tarjeta desde la app ahora.",
        "pt": "Como você compartilhou informações com esse contato, passei seu caso para um especialista em fraude (protocolo {case}), que entrará em contato pelos canais oficiais. Bloqueie seu cartão pelo app agora."},
    "ask_shared": {
        "es": "¿Llegó a compartir algún código, clave o dato de su tarjeta con ese contacto?",
        "pt": "Você chegou a compartilhar algum código, senha ou dado do cartão com esse contato?"},
    "out_of_scope": {
        "es": "Con eso no puedo ayudarle aquí: solo reviso cargos que no reconoce o cree incorrectos, y verifico contactos \"del banco\". Para otros temas use los canales oficiales del banco.",
        "pt": "Com isso não posso ajudar aqui: só reviso cobranças que você não reconhece ou acha erradas, e verifico contatos \"do banco\". Para outros assuntos, use os canais oficiais do banco."},
    "unauthorized": {
        "es": "Solo puedo consultar información de su propia cuenta. No puedo revisar datos de otras personas.",
        "pt": "Só posso consultar informações da sua própria conta. Não posso verificar dados de outras pessoas."},
    "session_expired": {
        "es": "Su sesión expiró por seguridad. Vuelva a iniciar sesión para continuar.",
        "pt": "Sua sessão expirou por segurança. Faça login novamente para continuar."},
    "fallback": {
        "es": "Tuve un problema técnico al consultar sus datos. Para no darle información incorrecta, pasé su consulta a una persona (folio {case}).",
        "pt": "Tive um problema técnico ao consultar seus dados. Para não dar informação incorreta, passei sua consulta para uma pessoa (protocolo {case})."},
    "closed": {
        "es": "Este caso ya está cerrado. Si quiere revisar otro cargo, dígame el monto, el comercio o la fecha.",
        "pt": "Este caso já está encerrado. Se quiser revisar outra cobrança, diga o valor, a loja ou a data."},
}

CHANNEL_NAMES = {
    "es": {"sms": "SMS", "whatsapp": "WhatsApp", "email": "correo", "push": "notificación de la app", "call": "llamada", "any": "ningún canal",
           "SMS": "SMS", "WhatsApp": "WhatsApp", "Email": "correo", "Push": "notificación de la app", "Voice": "llamada",
           "App": "app", "Web": "web", "POS": "terminal en comercio", "ATM": "cajero", "Branch": "sucursal", "Transfer": "transferencia"},
    "pt": {"sms": "SMS", "whatsapp": "WhatsApp", "email": "e-mail", "push": "notificação do app", "call": "ligação", "any": "nenhum canal",
           "SMS": "SMS", "WhatsApp": "WhatsApp", "Email": "e-mail", "Push": "notificação do app", "Voice": "ligação",
           "App": "app", "Web": "web", "POS": "maquininha na loja", "ATM": "caixa eletrônico", "Branch": "agência", "Transfer": "transferência"},
}
PRODUCT_NAMES = {
    "es": {"Tarjeta Crédito": "tarjeta de crédito", "Tarjeta Débito": "tarjeta de débito", "Cuenta Ahorro": "cuenta de ahorro",
           "Cuenta Corriente": "cuenta corriente", "Préstamo Personal": "préstamo personal", "Préstamo Hipotecario": "hipoteca",
           "Inversión": "inversión", "Seguro": "seguro"},
    "pt": {"Tarjeta Crédito": "cartão de crédito", "Tarjeta Débito": "cartão de débito", "Cuenta Ahorro": "conta poupança",
           "Cuenta Corriente": "conta corrente", "Préstamo Personal": "empréstimo pessoal", "Préstamo Hipotecario": "financiamento imobiliário",
           "Inversión": "investimento", "Seguro": "seguro"},
}
TX_KINDS = {
    "es": {"Payment": "pago", "Withdrawal": "retiro", "Transfer": "transferencia", "Adjustment": "ajuste", "Purchase": "compra"},
    "pt": {"Payment": "pagamento", "Withdrawal": "saque", "Transfer": "transferência", "Adjustment": "ajuste", "Purchase": "compra"},
}


def t(key: str, lang: str, **kw) -> str:
    return T[key][lang].format(**kw)
