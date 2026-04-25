from pymongo import MongoClient
from datetime import datetime
import random
import time
import threading

def get_db():
    client = MongoClient("mongodb://admin:motdepasse@localhost:27017/", authSource="admin")
    return client["terroir_local"]

CLIENTS = [
    {"nom": "Amadou Diallo", "email": "amadou.diallo@gmail.com", "telephone": "+221771234567", "ville": "Dakar"},
    {"nom": "Fatou Ndiaye", "email": "fatou.ndiaye@gmail.com", "telephone": "+221781234568", "ville": "Thies"},
    {"nom": "Moussa Sow", "email": "moussa.sow@gmail.com", "telephone": "+221701234569", "ville": "Saint-Louis"},
    {"nom": "Aissatou Ba", "email": "aissatou.ba@gmail.com", "telephone": "+221771234570", "ville": "Ziguinchor"},
    {"nom": "Ibrahima Fall", "email": "ibrahima.fall@gmail.com", "telephone": "+221781234571", "ville": "Kaolack"},
    {"nom": "Mariama Diop", "email": "mariama.diop@gmail.com", "telephone": "+221701234572", "ville": "Tambacounda"},
    {"nom": "Ousmane Gueye", "email": "ousmane.gueye@gmail.com", "telephone": "+221771234573", "ville": "Louga"},
    {"nom": "Rokhaya Sarr", "email": "rokhaya.sarr@gmail.com", "telephone": "+221781234574", "ville": "Fatick"},
    {"nom": "Cheikh Mbaye", "email": "cheikh.mbaye@gmail.com", "telephone": "+221701234575", "ville": "Diourbel"},
    {"nom": "Ndéye Thiam", "email": "ndeye.thiam@gmail.com", "telephone": "+221771234576", "ville": "Kolda"},
    {"nom": "Mamadou Cisse", "email": "mamadou.cisse@gmail.com", "telephone": "+221781234577", "ville": "Matam"},
    {"nom": "Binta Kouyate", "email": "binta.kouyate@gmail.com", "telephone": "+221701234578", "ville": "Kaffrine"},
    {"nom": "Seydou Badji", "email": "seydou.badji@gmail.com", "telephone": "+221771234579", "ville": "Kedougou"},
    {"nom": "Awa Mendy", "email": "awa.mendy@gmail.com", "telephone": "+221781234580", "ville": "Sedhiou"},
]

STATUTS = ["en_attente", "confirmee", "expediee", "livree"]
LIVRAISONS = ["express", "normal"]

REGIONS = [
    "Dakar", "Thies", "Saint-Louis", "Ziguinchor", "Kaolack",
    "Tambacounda", "Kolda", "Fatick", "Louga", "Matam",
    "Kaffrine", "Kedougou", "Sedhiou", "Diourbel"
]

def generer_commande_aleatoire():
    db = get_db()
    produits_disponibles = list(db.produits.find({"stock": {"$gt": 0}}))

    if not produits_disponibles:
        print("Aucun produit disponible !")
        return None

    nb_articles = random.randint(1, 3)
    produits_choisis = random.sample(produits_disponibles, min(nb_articles, len(produits_disponibles)))

    articles = []
    for produit in produits_choisis:
        quantite = random.randint(1, min(5, produit["stock"]))
        articles.append({
            "produit_id": produit["_id"],
            "nom_produit": produit["nom"],
            "quantite": quantite,
            "prix_unitaire": produit["prix"],
            "unite": produit.get("unite", "kg")
        })
        db.produits.update_one(
            {"_id": produit["_id"]},
            {"$inc": {"stock": -quantite}}
        )

    total = sum(a["quantite"] * a["prix_unitaire"] for a in articles)
    client = random.choice(CLIENTS)
    type_livraison = random.choice(LIVRAISONS)
    frais_livraison = 2000 if type_livraison == "express" else 500

    commande = {
        "client": client,
        "date": datetime.now(),
        "articles": articles,
        "statut": random.choice(STATUTS),
        "total": round(total, 2),
        "devise": "FCFA",
        "livraison": {
            "type": type_livraison,
            "frais": frais_livraison,
            "adresse": str(random.randint(1, 200)) + " rue de la Paix",
            "ville": client["ville"],
            "region": client["ville"]
        }
    }

    result = db.commandes.insert_one(commande)
    print("[" + datetime.now().strftime("%H:%M:%S") + "] Commande - " + client["nom"] + " - " + str(total) + " FCFA - " + type_livraison)
    return result.inserted_id

def demarrer_generateur(intervalle_secondes=60, nb_commandes=None):
    print("Generateur demarre (toutes les " + str(intervalle_secondes) + "s)")
    compteur = 0
    try:
        while True:
            if nb_commandes and compteur >= nb_commandes:
                print(str(nb_commandes) + " commandes generees. Arret.")
                break
            generer_commande_aleatoire()
            compteur += 1
            if nb_commandes is None or compteur < nb_commandes:
                time.sleep(intervalle_secondes)
    except KeyboardInterrupt:
        print("Generateur arrete. " + str(compteur) + " commandes creees.")

def demarrer_en_arriere_plan(intervalle_secondes=60):
    thread = threading.Thread(target=demarrer_generateur, args=(intervalle_secondes,), daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    print("Generation de 5 commandes initiales...")
    for i in range(5):
        generer_commande_aleatoire()
        time.sleep(1)
    print("Demarrage du generateur automatique...")
    demarrer_generateur(intervalle_secondes=60)
