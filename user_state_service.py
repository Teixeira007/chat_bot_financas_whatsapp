from firebase_config import db
from datetime import datetime
from google.cloud import firestore

def get_user_state(user):
    if not user:
        return None
    doc_ref = db.collection("usuarios").document(user)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        if data:
            return data.get("setup")
    return None

def set_user_state(user, state):
    db.collection("usuarios").document(user).set({"setup": state}, merge=True)

def clear_user_state(user):
    db.collection("usuarios").document(user).update({"setup": firestore.DELETE_FIELD})

def is_first_time_user(user):
    return not db.collection("usuarios").document(user).get().exists

def init_user(user):
    db.collection("usuarios").document(user).set({
        "setup": "limite_geral",
        "criado_em": datetime.now()
    })

def is_pending_reset(user):
    return get_user_state(user) == "confirmar_reset"

def mark_reset_pending(user):
    set_user_state(user, "confirmar_reset")

def reset_user_data(user):
    total = 0
    for col in ["usuarios", "limites", "gastos", "fixos"]:
        for doc in db.collection(col).where("user", "==", user).stream():
            doc.reference.delete()
            total += 1
    return total
