from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from utils import parse_add_comando
from gastos_service import salvar_gasto, buscar_gastos_por_categoria
from handlers import handle_fixo, handle_listar_fixos, handle_add, handle_gastos, handle_categoria_total, handle_ajuda, handle_categoria, handle_init, handle_limite, handle_saldo, handle_limites, handle_resumo, handle_setup_step
from user_state_service import get_user_state, set_user_state, is_pending_reset, reset_user_data, is_first_time_user, init_user
from limite_service import definir_limite, salvar_gasto_fixo
from firebase_config import db

app = Flask(__name__)

COMMANDS = {
    "add": handle_add,
    "gastos": handle_gastos,
    "categoria total": handle_categoria_total,
    "ajuda": handle_ajuda,
    "categoria": handle_categoria,
    "limite": handle_limite,
    "saldo": handle_saldo,
    "configuracação limites": handle_limites,
    "resumo": handle_resumo,
    "init": handle_init, 
    "fixo": handle_fixo, 
    "fixos": handle_listar_fixos,
}

@app.route("/webhook", methods=["POST"])
def webhook():
    msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")

    print(f"Mensagem recebida de {sender}: {msg}")

    resp = MessagingResponse()

    if is_first_time_user(sender):
        init_user(sender)
        resp.message(
            "👋 Olá! Bem-vindo ao seu assistente financeiro no WhatsApp!\n\n"
            "Vamos começar sua configuração inicial? 😄\n"
            "👉 *Qual é seu limite geral de gastos no mês (ex: 2500)?*"
        )
        return str(resp)

    if msg.lower() == "confirmar reset" and is_pending_reset(sender):
        total = reset_user_data(sender)
        set_user_state(sender, None)
        resp.message(
            f"🧨 Todos os seus dados foram apagados com sucesso ({total} registros).\n"
            "Se quiser recomeçar, digite `init` para iniciar novamente. 🚀"
        )
        return str(resp)

    estado = get_user_state(sender)

    if estado:
        return str(handle_setup_step(estado, msg, sender, resp))
    for comando, funcao in COMMANDS.items():
        if msg.lower().startswith(comando):
            funcao(msg, sender, resp)
            break
    else:
        resp.message("🤖 Comando não reconhecido. Use `/ajuda` para ver os disponíveis.")
    return str(resp)

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
