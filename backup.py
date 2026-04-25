import json
import os
import threading
import time
from datetime import datetime
from pymongo import MongoClient
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MONGO_URI, MONGO_AUTH_SOURCE, MONGO_DB, BACKUP_DIR
from logger import log_info, log_erreur

def get_db():
    client = MongoClient(MONGO_URI, authSource=MONGO_AUTH_SOURCE)
    return client[MONGO_DB]

def faire_backup():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        db = get_db()
        produits = list(db.produits.find({}, {"_id": 0}))
        commandes = list(db.commandes.find({}, {"_id": 0, "articles.produit_id": 0}))
        for c in commandes:
            c["date"] = str(c.get("date", ""))
        backup = {
            "date": str(datetime.now()),
            "nb_produits": len(produits),
            "nb_commandes": len(commandes),
            "produits": produits,
            "commandes": commandes
        }
        nom_fichier = os.path.join(BACKUP_DIR, "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
        with open(nom_fichier, "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2, default=str)
        fichiers = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")])
        while len(fichiers) > 7:
            os.remove(os.path.join(BACKUP_DIR, fichiers.pop(0)))
        log_info("Backup cree : " + nom_fichier)
        return nom_fichier
    except Exception as e:
        log_erreur("Erreur backup : " + str(e))
        return None

def demarrer_backup_automatique(intervalle_heures=24):
    def run():
        while True:
            faire_backup()
            time.sleep(intervalle_heures * 3600)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    log_info("Backup automatique demarre (toutes les " + str(intervalle_heures) + "h)")
    return thread

def lister_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    return sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")])

if __name__ == "__main__":
    fichier = faire_backup()
    print("Backup cree : " + str(fichier))
    print("Backups disponibles :")
    for f in lister_backups():
        taille = os.path.getsize(os.path.join(BACKUP_DIR, f))
        print("  - " + f + " (" + str(taille) + " octets)")
