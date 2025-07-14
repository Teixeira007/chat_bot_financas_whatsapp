from firebase_config import db
from datetime import datetime


def definir_limite(user, valor, categoria=None):
    mes = datetime.now().strftime("%Y-%m")
    tipo = "categoria" if categoria else "geral"

    filtro = db.collection("limites") \
        .where("user", "==", user) \
        .where("mes", "==", mes) \
        .where("tipo", "==", tipo)

    if categoria:
        filtro = filtro.where("categoria", "==", categoria)

    docs = list(filtro.stream())

    if docs:
        for doc in docs:
            doc.reference.update({"valor": valor})
    else:
        doc = {
            "user": user,
            "tipo": tipo,
            "categoria": categoria if categoria else None,
            "valor": valor,
            "mes": mes
        }
        db.collection("limites").add(doc)


def buscar_limite(user, categoria=None):
    mes = datetime.now().strftime("%Y-%m")
    filtro = db.collection("limites").where("user", "==", user).where("mes", "==", mes)

    if categoria:
        filtro = filtro.where("tipo", "==", "categoria").where("categoria", "==", categoria)
    else:
        filtro = filtro.where("tipo", "==", "geral")

    docs = list(filtro.stream())
    if not docs:
        return None
    doc_dict = docs[0].to_dict()
    return doc_dict.get("valor") if doc_dict else None


def buscar_todos_limites(user):
    mes = datetime.now().strftime("%Y-%m")
    docs = db.collection("limites").where("user", "==", user).where("mes", "==", mes).stream()
    return [doc.to_dict() for doc in docs]

def salvar_gasto_fixo(user, nome, valor):
    db.collection("fixos").add({
        "user": user,
        "nome": nome,
        "valor": valor,
        "criado_em": datetime.now()
    })
