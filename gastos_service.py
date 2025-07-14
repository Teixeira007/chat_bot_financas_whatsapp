from datetime import datetime
from firebase_config import db

def salvar_gasto(user, categoria, descricao, valor):
    doc = {
        "user": user,
        "categoria": categoria,
        "descricao": descricao,
        "valor": valor,
        "data": datetime.now().isoformat()
    }
    db.collection("gastos").add(doc)

def buscar_gastos_por_categoria(user, categoria):
    docs = db.collection("gastos").where("user", "==", user).where("categoria", "==", categoria).stream()
    return [doc.to_dict() for doc in docs]

def buscar_gastos_filtrados(user, categoria=None, periodo=None, ano=None):
    docs = db.collection("gastos").where("user", "==", user).stream()
    gastos = []

    hoje = datetime.now().date().isoformat()
    mes_atual = datetime.now().strftime("%Y-%m")
    ano_atual = datetime.now().year

    for doc in docs:
        d = doc.to_dict()
        data = d.get("data", "")
        data_obj = datetime.fromisoformat(data)

        if categoria and d["categoria"].lower() != categoria.lower():
            continue

        if periodo == "hoje" and not data.startswith(hoje):
            continue
        elif periodo == "mes" and not data.startswith(mes_atual):
            continue
        elif periodo == "ano":
            ano_uso = int(ano) if ano else ano_atual
            if data_obj.year != ano_uso:
                continue

        gastos.append(d)

    return gastos

def buscar_total_categoria(user, categoria):
    docs = db.collection("gastos").where("user", "==", user).where("categoria", "==", categoria).stream()
    return sum(doc.to_dict().get("valor", 0) for doc in docs)

def buscar_total_gastos_fixos(user):
    docs = db.collection("fixos").where("user", "==", user).stream()
    total = 0
    for doc in docs:
        data = doc.to_dict()
        total += data.get("valor", 0)
    return total

def listar_gastos_fixos(user):
    docs = db.collection("fixos").where("user", "==", user).stream()
    fixos = []
    for doc in docs:
        data = doc.to_dict()
        fixos.append({
            "nome": data.get("nome", "desconhecido"),
            "valor": data.get("valor", 0)
        })
    return fixos


