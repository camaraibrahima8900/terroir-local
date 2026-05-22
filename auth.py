import bcrypt
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_DIR, USERS_FILE
from logger import log_info, log_erreur, log_warning

def hasher_mot_de_passe(mot_de_passe):
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verifier_mot_de_passe(mot_de_passe, hash_stocke):
    return bcrypt.checkpw(mot_de_passe.encode("utf-8"), hash_stocke.encode("utf-8"))

def creer_utilisateurs_defaut():
    users = {
        "admin": {
            "password": hasher_mot_de_passe("admin123"),
            "role": "administrateur",
            "nom": "Administrateur",
            "email": "admin@terroirlocal.sn"
        },
        "user": {
            "password": hasher_mot_de_passe("user123"),
            "role": "utilisateur",
            "nom": "Utilisateur",
            "email": "user@terroirlocal.sn"
        }
    }
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    log_info("Utilisateurs par defaut crees !")
    return users

def charger_utilisateurs():
    if not os.path.exists(USERS_FILE):
        return creer_utilisateurs_defaut()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def authentifier(username, password):
    try:
        users = charger_utilisateurs()
        if username not in users:
            log_warning("Utilisateur inconnu : " + username)
            return None
        if users[username].get("bloque", False):
            log_warning("Compte bloque : " + username)
            return "BLOQUE"
        if verifier_mot_de_passe(password, users[username]["password"]):
            log_info("Connexion reussie : " + username)
            return users[username]["role"]
        else:
            log_warning("Mot de passe incorrect : " + username)
            return None
    except Exception as e:
        log_erreur("Erreur auth : " + str(e))
        return None

def ajouter_utilisateur(login, password, role="utilisateur", nom="", email="", cree_par="admin", telephone="", lieu=""):
    try:
        users = charger_utilisateurs()
        if login in users:
            return False, "Utilisateur deja existant !"
        users[login] = {
            "password": hasher_mot_de_passe(password),
            "role": role,
            "nom": nom,
            "email": email,
            "cree_par": cree_par,
            "telephone": telephone,
            "lieu": lieu,
            "bloque": False
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        log_info("Utilisateur cree : " + login)
        return True, "Utilisateur cree !"
    except Exception as e:
        return False, str(e)

def supprimer_utilisateur(username):
    try:
        users = charger_utilisateurs()
        if username not in users:
            return False, "Utilisateur introuvable !"
        if username == "admin":
            return False, "Impossible de supprimer l'admin principal !"
        del users[username]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        log_info("Utilisateur supprime : " + username)
        return True, "Utilisateur supprime !"
    except Exception as e:
        return False, str(e)

def charger_users():
    return charger_utilisateurs()

def sauvegarder_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        import json
        json.dump(users, f, indent=2, ensure_ascii=False)

def lister_utilisateurs():
    users = charger_utilisateurs()
    return [
        (
            u,                                    # 0 login
            users[u]["role"],                    # 1 role
            users[u].get("nom",""),              # 2 nom
            users[u].get("email",""),            # 3 email
            users[u].get("telephone",""),        # 4 telephone
            users[u].get("lieu",""),             # 5 lieu
            users[u].get("photo",""),            # 6 photo
            users[u].get("cree_par","admin"),    # 7 cree_par
            users[u].get("bloque", False)        # 8 bloque
        )
        for u in users
    ]

if __name__ == "__main__":
    creer_utilisateurs_defaut()
    print("Test admin   :", authentifier("admin", "admin123"))
    print("Test user    :", authentifier("user", "user123"))
    print("Test mauvais :", authentifier("admin", "mauvais"))
