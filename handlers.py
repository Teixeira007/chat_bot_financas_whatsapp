# handlers.py
from datetime import datetime
from firebase_config import db
from user_state_service import mark_reset_pending
from twilio.twiml.messaging_response import MessagingResponse



def handle_add(msg, sender, resposta):
    from utils import parse_add_comando
    from gastos_service import salvar_gasto
    parsed = parse_add_comando(msg)
    if parsed:
        categoria, descricao, valor = parsed
        salvar_gasto(sender, categoria, descricao, valor)
        resposta.message(f"✅ Gasto salvo: *{descricao}* em _{categoria}_ R${valor:.2f}")
    else:
        resposta.message("❌ Formato inválido. Use: `add categoria descrição valor`")


def handle_gastos(msg, sender, resposta):
    from gastos_service import buscar_gastos_filtrados
    partes = msg.lower().split()

    filtro_categoria = None
    filtro_periodo = "geral"
    filtro_ano = None

    # Ex: /gastos categoria comida mes
    if "categoria" in partes:
        idx = partes.index("categoria")
        if len(partes) > idx + 1:
            filtro_categoria = partes[idx + 1]

    if "hoje" in partes:
        filtro_periodo = "hoje"
    elif "mes" in partes:
        filtro_periodo = "mes"
    elif "ano" in partes:
        filtro_periodo = "ano"
        idx = partes.index("ano")
        if len(partes) > idx + 1:
            filtro_ano = partes[idx + 1]

    gastos = buscar_gastos_filtrados(sender, categoria=filtro_categoria, periodo=filtro_periodo, ano=filtro_ano)
    total = sum(g["valor"] for g in gastos)

    if not gastos:
        resposta.message("📊 Nenhum gasto encontrado com esse filtro.")
        return
  # Construção da mensagem
    now = datetime.now()
    descricao_periodo = {
        "geral": "no geral",
        "hoje": "hoje",
        "mes": f"em {now.strftime('%B/%Y')}",
        "ano": f"em {filtro_ano or now.year}"
    }

    if filtro_categoria:
        emoji = "🍔" if filtro_categoria == "comida" else "💸"
        texto = f"{emoji} Total gasto com *{filtro_categoria}* {descricao_periodo[filtro_periodo]}: R${total:.2f}"
    else:
        prefixo = {
            "geral": "📊",
            "hoje": "📆",
            "mes": "📅",
            "ano": "📆"
        }.get(filtro_periodo, "📊")
        texto = f"{prefixo} Total gasto {descricao_periodo[filtro_periodo]}: R${total:.2f}"
    for g in gastos:
        texto += f"- {g['descricao']} ({g['categoria']}): R${g['valor']:.2f}\n"
    resposta.message(texto)


def handle_categoria_total(msg, sender, resposta):
    from gastos_service import buscar_total_categoria
    partes = msg.split(" ", 1)
    if len(partes) < 2:
        resposta.message("❗ Informe a categoria. Ex: `/categoria transporte`")
    else:
        categoria = partes[1].strip().lower()
        total = buscar_total_categoria(sender, categoria)
        resposta.message(f"📂 Total em *{categoria}*: R${total:.2f}")

def handle_categoria(msg, sender, resposta):
    from gastos_service import buscar_gastos_por_categoria
    partes = msg.split(" ", 1)
    if len(partes) < 2:
        resposta.message("❗ Informe a categoria. Ex: `/categoria transporte`")
    else:
        categoria = partes[1].strip().lower()
        gastos = buscar_gastos_por_categoria(sender, categoria)
        if gastos:
            resposta.message(f"📂 *Gastos em {categoria}:*\n{'\n'.join([f'{g['descricao']} - R${g['valor']:.2f}' for g in gastos])}")
        else:
            resposta.message(f"✅ Nenhum gasto em {categoria} encontrado.")


def handle_ajuda(_, __, resposta):
    resposta.message(
        "🤖 *Bot de Gastos - Comandos Disponíveis*\n"
        "Organize suas finanças direto pelo WhatsApp 💸\n\n"

        "🟢 *Adicionar gasto:*\n"
        "`add categoria descrição valor`\n"
        "Ex: `add comida pizza 35.90`\n\n"

        "📊 *Consultar gastos:*\n"
        "`/gastos` – Total geral\n"
        "`/gastos mes` – Total do mês atual\n"
        "`/gastos hoje` – Total de hoje\n"
        "`/gastos ano 2024` – Total em um ano específico\n"
        "`/gastos categoria comida mes` – Gasto por categoria + período\n\n"

        "📂 *Categorias:* \n"
        "`/categoria nome` – Total gasto em uma categoria\n"
        "Ex: `/categoria transporte`\n\n"

        "📅 *Relatórios:* \n"
        "`/resumo` – Relatório mensal: total, saldo e categorias\n"
        

        "📏 *Limites:*\n"
        "`/limite 2000` – Define limite geral mensal\n"
        "`/limite comida 400` – Define limite para uma categoria\n"
        "`/limites` – Lista todos os limites definidos\n"
        "`/saldo` – Mostra quanto ainda pode gastar (geral)\n"
        "`/saldo comida` – Mostra saldo de uma categoria específica\n\n"

        "❓ *Ajuda:*\n"
        "`/ajuda` – Exibe essa mensagem\n\n"

        "💡 *Dica:* Use comandos simples, como se estivesse mandando mensagem.\n"
        "Seu histórico financeiro nunca foi tão fácil de manter! 😄"
    )

def handle_limite(msg, sender, resposta):
    from limite_service import definir_limite, buscar_limite, buscar_todos_limites

    partes = msg.lower().split()
    if len(partes) == 2:
        # Limite geral
        try:
            valor = float(partes[1].replace(",", "."))
            definir_limite(sender, valor)
            resposta.message(f"✅ Limite geral mensal definido: R${valor:.2f}")
        except ValueError:
            resposta.message("❌ Valor inválido. Use: `/limite 2000`")
    elif len(partes) == 3:
        # Limite por categoria
        categoria = partes[1]
        try:
            valor = float(partes[2].replace(",", "."))
            definir_limite(sender, valor, categoria)
            resposta.message(f"✅ Limite para *{categoria}* definido: R${valor:.2f}")
        except ValueError:
            resposta.message("❌ Valor inválido. Use: `/limite comida 400`")
    else:
        resposta.message("❌ Formato inválido. Use:\n`/limite 2000`\n`/limite comida 400`")


def handle_saldo(msg, sender, resposta):
    from gastos_service import buscar_gastos_filtrados, buscar_total_gastos_fixos
    from limite_service import buscar_limite

    partes = msg.lower().split()
    categoria = partes[1] if len(partes) == 2 else None

    limite = buscar_limite(sender, categoria)
    if limite is None:
        resposta.message("⚠️ Você ainda não configurou um limite geral. Use o comando `limite` para isso.")
        return

    gastos = buscar_gastos_filtrados(sender, categoria=categoria, periodo="mes")
    total_gasto = sum(g["valor"] for g in gastos)
    total_fixos = buscar_total_gastos_fixos(sender)

    saldo = limite - total_gasto - total_fixos

    texto = f"💰 Limite: R${limite:.2f}\n"
    texto += f"💸 Gasto no mês: R${(total_gasto+total_fixos):.2f}\n"
    texto += f"💸 Gasto adicionais no mês: R${total_gasto:.2f}\n"
    texto += f"💸 Gasto fixos do mês: R${(total_fixos):.2f}\n"
    texto += f"🟢 Saldo restante: R${saldo:.2f}" if saldo >= 0 else f"🔴 Excedeu o limite em R${-saldo:.2f}"
    resposta.message(texto)


def handle_limites(_, sender, resposta):
    from limite_service import buscar_todos_limites

    limites = buscar_todos_limites(sender)
    if not limites:
        resposta.message("⚠️ Nenhum limite configurado.")
        return

    texto = "📏 *Limites atuais:*\n"
    for l in limites:
        if l["tipo"] == "geral":
            texto += f"• Geral: R${l['valor']:.2f}\n"
        else:
            texto += f"• {l['categoria'].capitalize()}: R${l['valor']:.2f}\n"
    resposta.message(texto)

def handle_fixo(msg, user, resp):
    from limite_service import salvar_gasto_fixo
    partes = msg.strip().split()
    if len(partes) < 3 or partes[0].lower() != "fixo":
         resp.message("❌ Formato inválido. Use:\n`fixo nome_do_gasto valor`\nExemplo: `fixo aluguel 1200`")
    else:
        nome = " ".join(partes[1:-1])
        try:
            valor = float(partes[-1].replace(",", "."))
            salvar_gasto_fixo(user, nome, valor)
            resp.message(f"💾 Gasto fixo `{nome}` de R$ {valor:.2f} salvo com sucesso.")
        except:
            resp.message("❌ Formato inválido. Use:\n`fixo nome_do_gasto valor`\nExemplo: `fixo aluguel 1200`")

def handle_resumo(_, sender, resposta):
    from gastos_service import buscar_gastos_filtrados, buscar_total_gastos_fixos, listar_gastos_fixos
    from limite_service import buscar_limite, buscar_todos_limites
    from collections import defaultdict

    now = datetime.now()
    mes_label = now.strftime("%B/%Y").capitalize()

    # Gastos do mês
    gastos = buscar_gastos_filtrados(sender, periodo="mes")
    total_fixos = buscar_total_gastos_fixos(sender)

    total_gasto_adicionais = sum(g["valor"] for g in gastos)

    # Limite geral
    limite_geral = buscar_limite(sender)
    saldo_geral = limite_geral - total_gasto_adicionais - total_fixos if limite_geral else None
    total_gasto = total_gasto_adicionais + total_fixos

    # Agrupar gastos por categoria
    categorias = defaultdict(float)
    for g in gastos:
        categorias[g["categoria"]] += g["valor"]

    limites = buscar_todos_limites(sender)
    limites_dict = {l["categoria"]: l["valor"] for l in limites if l["tipo"] == "categoria"}

    texto = f"📊 *Resumo de {mes_label}*\n\n"
    texto += f"• Total gasto: R${total_gasto:.2f}\n"
    texto += f"• Total gastos adicionais: R${total_gasto_adicionais:.2f}\n"


    if limite_geral:
        if saldo_geral is not None and saldo_geral >= 0:
            texto += f"• Saldo geral restante: R${saldo_geral:.2f}\n"
        else:
            texto += f"• ⚠️ Excedeu o limite geral em R${-saldo_geral:.2f}\n" if saldo_geral is not None else "• ⚠️ Nenhum limite geral definido\n"
    else:
        texto += f"• Nenhum limite geral definido\n"

    texto += "\n📂 *Por categoria:*\n"
    for cat, valor in categorias.items():
        limite = limites_dict.get(cat)
        if limite:
            saldo = limite - valor
            if saldo >= 0:
                texto += f"• {cat.capitalize()}: R${valor:.2f} (Limite: R${limite:.2f}, Saldo: R${saldo:.2f})\n"
            else:
                texto += f"• {cat.capitalize()}: R${valor:.2f} (Limite: R${limite:.2f}, Excedeu R${-saldo:.2f})\n"
        else:
            texto += f"• {cat.capitalize()}: R${valor:.2f} (Sem limite)\n"

    texto += "\n📂 *Totais fixos:*\n"
    gastos_fixos = listar_gastos_fixos(sender)
    if not gastos_fixos:
        texto += "• Nenhum gasto fixo cadastrado\n"
    else:
        for fixo in gastos_fixos:
            texto += f"• {fixo['nome']} — R$ {fixo['valor']:.2f}\n"
        texto += f"💰 Total fixos: R$ {total_fixos:.2f}\n"
    resposta.message(texto)

def handle_init(msg, user, resp):
    # Parte 1: Boas-vindas e explicações
    mensagem = (
        "👋 Olá! Bem-vindo ao seu assistente financeiro pessoal no WhatsApp!\n\n"
        "Comigo você pode:\n"
        "📌 Registrar seus gastos\n"
        "📊 Ver saldos e resumos\n"
        "🛑 Definir limites por categoria\n"
        "💸 Acompanhar tudo direto aqui, sem complicação!\n\n"
        "Vamos começar sua configuração inicial? 😄\n"
        "👉 *Qual é seu limite geral de gastos no mês (ex: seu salário)?*"
    )
    # Marcar no Firestore ou em cache que o usuário está em processo de setup
    db.collection("usuarios").document(user).set({"setup": "limite_geral"}, merge=True)
    resp.message(mensagem)

def handle_reset(msg, user, resp):
    mark_reset_pending(user)
    resp.message(
        "⚠️ Tem certeza que deseja apagar *todos os seus dados*?\n"
        "Se sim, digite:\n`confirmar reset`\n\n"
        "❌ Para cancelar, basta ignorar esta mensagem."
    )

def handle_setup_step(estado, msg, user, resp: MessagingResponse):
    from limite_service import definir_limite, salvar_gasto_fixo
    from user_state_service import set_user_state


    if estado == "limite_geral":
        try:
            valor = float(msg.replace(",", "."))
            definir_limite(user, valor)
            set_user_state(user, "limites_categoria")
            resp.message(
                f"✅ Limite mensal salvo: R$ {valor:.2f}\n\n"
                "Agora, você pode configurar limites por categoria (ex: limite mercado 600), ou digite `pular` para continuar."
            )
        except:
            resp.message("❌ Valor inválido. Envie apenas o número (ex: 2500).")

    elif estado == "limites_categoria":
        if msg.lower() == "pular":
            set_user_state(user, "gastos_fixos")
            resp.message(
                "👍 Beleza! Agora vamos configurar gastos fixos (ex: aluguel, celular, etc).\n\n"
                "Envie no formato: `fixo aluguel 1200`\nOu digite `fim` para encerrar."
            )
        elif msg.lower().startswith("limite "):
            partes = msg.split(" ")
            if len(partes) >= 3:
                categoria = partes[1]
                try:
                    valor = float(partes[2].replace(",", "."))
                    definir_limite(user, valor, categoria)
                    resp.message(f"💾 Limite da categoria `{categoria}` salvo: R$ {valor:.2f}")
                except:
                    resp.message("❌ Valor inválido. Use: `limite mercado 500`")
            else:
                resp.message("❌ Formato inválido. Use: `limite mercado 500`")
        else:
            resp.message("💡 Envie `limite categoria valor` ou `pular` para seguir.")

    elif estado == "gastos_fixos":
        if msg.lower() == "fim":
            set_user_state(user, None)
            resp.message("🎉 Configuração concluída! Agora você pode usar todos os comandos. Digite `ajuda` para ver. 🚀")
        elif msg.lower().startswith("fixo "):
            partes = msg.strip().split()
            if len(partes) < 3 or partes[0].lower() != "fixo":
                resp.message("❌ Use: `fixo nome valor`")
            else:
                nome = " ".join(partes[1:-1])
                try:
                    valor = float(partes[-1].replace(",", "."))
                    salvar_gasto_fixo(user, nome, valor)
                    resp.message(f"💾 Gasto fixo `{nome}` de R$ {valor:.2f} salvo.")
                except:
                    resp.message("❌ Valor inválido.")
        else:
            resp.message("💡 Use `fixo nome valor` ou `fim`.")

    return resp

def handle_listar_fixos(msg, user, resp):
    from gastos_service import listar_gastos_fixos
    fixos = listar_gastos_fixos(user)
    
    if not fixos:
        resp.message("📎 Você ainda não tem nenhum gasto fixo cadastrado.")
        return

    texto = "📎 *Seus gastos fixos mensais:*\n"
    total = 0
    for gasto in fixos:
        texto += f"• {gasto['nome']} — R$ {gasto['valor']:.2f}\n"
        total += gasto['valor']

    texto += f"💰 *Total:* R$ {total:.2f}"
    resp.message(texto)