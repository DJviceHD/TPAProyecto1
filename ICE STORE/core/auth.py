import json
from pathlib import Path
import re

USERS_FILE = Path(__file__).parent.parent / 'data' / 'users.json'

def load_users():
    return json.loads(USERS_FILE.read_text(encoding='utf-8'))

def save_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

def authenticate(email, password):
    for u in load_users().get("users", []):
        if u["email"] == email and u["password"] == password:
            return u
    return None

def register_user(email, password):
    if "@" not in email:
        return False, "El correo debe contener '@'."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número."
    data = load_users()
    for u in data.get("users", []):
        if u["email"] == email:
            return False, "El correo ya está registrado."
    data["users"].append({"email": email, "password": password})
    save_users(data)
    return True, "Usuario registrado exitosamente."
