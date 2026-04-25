import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import random

from config import MONGO_URI, MONGO_AUTH_SOURCE, MONGO_DB, FRAIS_LIVRAISON, DEVISE, APP_NOM
from auth import authentifier, lister_utilisateurs, ajouter_utilisateur, supprimer_utilisateur
from logger import log_info, log_erreur
from backup import faire_backup, lister_backups, demarrer_backup_automatique

app = Flask(__name__)
app.secret_key = "terroir_local_senegal_2025_secret"

REGIONS = [
    "Dakar", "Thies", "Saint-Louis", "Ziguinchor", "Kaolack",
    "Tambacounda", "Kolda", "Fatick", "Louga", "Matam",
    "Kaffrine", "Kedougou", "Sedhiou", "Diourbel"
]

CATEGORIES = ["Fruits", "Legumes", "Cereales", "Huiles", "Poissons"]

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
    {"nom": "Ndeye Thiam", "email": "ndeye.thiam@gmail.com", "telephone": "+221771234576", "ville": "Kolda"},
    {"nom": "Mamadou Cisse", "email": "mamadou.cisse@gmail.com", "telephone": "+221781234577", "ville": "Matam"},
    {"nom": "Binta Kouyate", "email": "binta.kouyate@gmail.com", "telephone": "+221701234578", "ville": "Kaffrine"},
    {"nom": "Seydou Badji", "email": "seydou.badji@gmail.com", "telephone": "+221771234579", "ville": "Kedougou"},
    {"nom": "Awa Mendy", "email": "awa.mendy@gmail.com", "telephone": "+221781234580", "ville": "Sedhiou"},
]

def get_db():
    try:
        client = MongoClient(MONGO_URI, authSource=MONGO_AUTH_SOURCE, serverSelectionTimeoutMS=3000)
        client.server_info()
        return client[MONGO_DB]
    except Exception as e:
        log_erreur("Connexion MongoDB echouee : " + str(e))
        return None

def login_requis(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "role" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_requis(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "administrateur":
            return redirect(url_for("boutique"))
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET", "POST"])
def login():
    if "role" in session:
        return redirect(url_for("boutique"))
    erreur = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = authentifier(username, password)
        if role:
            session["username"] = username
            session["role"] = role
            return redirect(url_for("boutique"))
        else:
            erreur = "Identifiants incorrects !"
    return render_template("login.html", erreur=erreur)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/boutique")
@login_requis
def boutique():
    db = get_db()
    if db is None:
        return "<h1>Erreur connexion MongoDB</h1>"
    filtre = {}
    categorie = request.args.get("categorie", "Toutes")
    search = request.args.get("search", "")
    promo = int(request.args.get("promo", 0))
    if categorie != "Toutes":
        filtre["categorie"] = categorie
    if search:
        filtre["nom"] = {"$regex": search, "$options": "i"}
    produits = list(db.produits.find(filtre).sort("categorie", 1))
    for p in produits:
        p["_id"] = str(p["_id"])
        p["prix_final"] = int(p["prix"] * (1 - promo / 100))
        p["promo"] = promo
    panier = session.get("panier", [])
    total = sum(i["quantite"] * i["prix_final"] for i in panier)
    return render_template("boutique.html",
        produits=produits, categories=CATEGORIES, regions=REGIONS,
        categorie=categorie, search=search, promo=promo,
        panier=panier, total=total, role=session.get("role"),
        username=session.get("username"), devise=DEVISE)

@app.route("/ajouter_panier", methods=["POST"])
@login_requis
def ajouter_panier():
    produit_id = request.form.get("produit_id")
    quantite = int(request.form.get("quantite", 1))
    promo = int(request.form.get("promo", 0))
    db = get_db()
    if db is None:
        return redirect(url_for("boutique"))
    produit = db.produits.find_one({"_id": ObjectId(produit_id)})
    if not produit or produit["stock"] < quantite:
        return redirect(url_for("boutique"))
    panier = session.get("panier", [])
    prix_final = int(produit["prix"] * (1 - promo / 100))
    panier.append({
        "produit_id": produit_id,
        "nom": produit["nom"],
        "quantite": quantite,
        "prix_unitaire": produit["prix"],
        "prix_final": prix_final,
        "promo": promo,
        "unite": produit.get("unite", "kg"),
        "image": produit.get("image", "📦")
    })
    session["panier"] = panier
    session.modified = True
    return redirect(url_for("boutique"))

@app.route("/retirer_panier/<int:index>")
@login_requis
def retirer_panier(index):
    panier = session.get("panier", [])
    if 0 <= index < len(panier):
        panier.pop(index)
    session["panier"] = panier
    session.modified = True
    return redirect(url_for("boutique"))

@app.route("/vider_panier")
@login_requis
def vider_panier():
    session["panier"] = []
    session.modified = True
    return redirect(url_for("boutique"))

@app.route("/commander", methods=["POST"])
@login_requis
def commander():
    panier = session.get("panier", [])
    if not panier:
        return redirect(url_for("boutique"))
    db = get_db()
    if db is None:
        return redirect(url_for("boutique"))
    region = request.form.get("region", "Dakar")
    type_livraison = request.form.get("livraison", "normal")
    frais = FRAIS_LIVRAISON.get(type_livraison, 500)
    client = random.choice(CLIENTS)
    sous_total = sum(i["quantite"] * i["prix_unitaire"] for i in panier)
    total_final = sum(i["quantite"] * i["prix_final"] for i in panier)
    reduction = sous_total - total_final
    total_avec_frais = total_final + frais
    commande = {
        "client": client,
        "date": datetime.now(),
        "articles": panier.copy(),
        "statut": "en_attente",
        "sous_total": round(sous_total, 2),
        "reduction": round(reduction, 2),
        "total": round(total_avec_frais, 2),
        "devise": DEVISE,
        "livraison": {
            "type": type_livraison,
            "frais": frais,
            "ville": region,
            "region": region
        }
    }
    for item in panier:
        db.produits.update_one(
            {"_id": ObjectId(item["produit_id"])},
            {"$inc": {"stock": -item["quantite"]}}
        )
    db.commandes.insert_one(commande)
    log_info("Commande - " + client["nom"] + " - " + str(total_avec_frais) + " FCFA")
    session["panier"] = []
    session.modified = True
    return render_template("confirmation.html",
        client=client, region=region, type_livraison=type_livraison,
        frais=frais, sous_total=sous_total, reduction=reduction,
        total=total_avec_frais, devise=DEVISE)

@app.route("/stats")
@login_requis
@admin_requis
def stats():
    db = get_db()
    if db is None:
        return "<h1>Erreur MongoDB</h1>"
    nb_produits = db.produits.count_documents({})
    nb_commandes = db.commandes.count_documents({})
    nb_ruptures = db.produits.count_documents({"stock": {"$lt": 5}})
    agg = list(db.commandes.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total"}, "moyenne": {"$avg": "$total"}}}]))
    ca_total = round(agg[0]["total"], 2) if agg else 0
    panier_moyen = round(agg[0]["moyenne"], 2) if agg else 0
    pipeline_cat = [
        {"$unwind": "$articles"},
        {"$lookup": {"from": "produits", "localField": "articles.produit_id", "foreignField": "_id", "as": "info"}},
        {"$unwind": "$info"},
        {"$group": {"_id": "$info.categorie", "ca": {"$sum": {"$multiply": ["$articles.quantite", "$articles.prix_unitaire"]}}, "qte": {"$sum": "$articles.quantite"}}},
        {"$sort": {"ca": -1}}
    ]
    ca_categories = list(db.commandes.aggregate(pipeline_cat))
    pipeline_region = [{"$group": {"_id": "$livraison.region", "nb": {"$sum": 1}, "ca": {"$sum": "$total"}}}, {"$sort": {"ca": -1}}]
    ca_regions = [r for r in db.commandes.aggregate(pipeline_region) if r["_id"]]
    top_produits = list(db.commandes.aggregate([
        {"$unwind": "$articles"},
        {"$group": {"_id": "$articles.produit_id", "nom": {"$first": "$articles.nom_produit"}, "qte": {"$sum": "$articles.quantite"}}},
        {"$sort": {"qte": -1}}, {"$limit": 5}
    ]))
    ruptures = list(db.produits.find({"stock": {"$lt": 5}}).sort("stock", 1))
    top_clients = list(db.commandes.aggregate([
        {"$group": {"_id": "$client.email", "nom": {"$first": "$client.nom"}, "tel": {"$first": "$client.telephone"}, "ville": {"$first": "$client.ville"}, "nb": {"$sum": 1}, "total": {"$sum": "$total"}}},
        {"$sort": {"total": -1}}, {"$limit": 10}
    ]))
    return render_template("stats.html",
        nb_produits=nb_produits, nb_commandes=nb_commandes,
        nb_ruptures=nb_ruptures, ca_total=ca_total,
        panier_moyen=panier_moyen, ca_categories=ca_categories,
        ca_regions=ca_regions, top_produits=top_produits,
        ruptures=ruptures, top_clients=top_clients,
        devise=DEVISE, role=session.get("role"),
        username=session.get("username"))

@app.route("/admin")
@login_requis
@admin_requis
def admin():
    db = get_db()
    produits = list(db.produits.find({}).sort("nom", 1)) if db is not None else []
    for p in produits:
        p["_id"] = str(p["_id"])
    users = lister_utilisateurs()
    backups = lister_backups()
    return render_template("admin.html",
        produits=produits, users=users, backups=backups,
        categories=CATEGORIES, regions=REGIONS,
        role=session.get("role"), username=session.get("username"))

@app.route("/admin/ajouter_produit", methods=["POST"])
@login_requis
@admin_requis
def ajouter_produit():
    db = get_db()
    if db is None:
        return redirect(url_for("admin"))
    nom = request.form.get("nom", "").strip()
    categorie = request.form.get("categorie", "").strip()
    prix = int(request.form.get("prix", 0))
    stock = int(request.form.get("stock", 0))
    unite = request.form.get("unite", "kg").strip()
    producteur = request.form.get("producteur", "").strip()
    origine = request.form.get("origine", "").strip()
    image = request.form.get("image", "📦").strip()
    if nom and categorie and prix and stock and producteur:
        db.produits.insert_one({
            "nom": nom, "categorie": categorie, "prix": prix,
            "stock": stock, "unite": unite, "producteur": producteur,
            "image": image, "attributs": {"origine": origine, "bio": False}
        })
        log_info("Produit ajoute : " + nom)
    return redirect(url_for("admin"))

@app.route("/admin/supprimer_produit/<produit_id>")
@login_requis
@admin_requis
def supprimer_produit(produit_id):
    db = get_db()
    if db is not None:
        db.produits.delete_one({"_id": ObjectId(produit_id)})
        log_info("Produit supprime : " + produit_id)
    return redirect(url_for("admin"))

@app.route("/admin/maj_stock", methods=["POST"])
@login_requis
@admin_requis
def maj_stock():
    db = get_db()
    if db is None:
        return redirect(url_for("admin"))
    produit_id = request.form.get("produit_id")
    stock = int(request.form.get("stock", 0))
    db.produits.update_one({"_id": ObjectId(produit_id)}, {"$set": {"stock": stock}})
    log_info("Stock mis a jour : " + str(stock))
    return redirect(url_for("admin"))

@app.route("/admin/maj_prix", methods=["POST"])
@login_requis
@admin_requis
def maj_prix():
    db = get_db()
    if db is None:
        return redirect(url_for("admin"))
    produit_id = request.form.get("produit_id")
    prix = int(request.form.get("prix", 0))
    db.produits.update_one({"_id": ObjectId(produit_id)}, {"$set": {"prix": prix}})
    log_info("Prix mis a jour : " + str(prix))
    return redirect(url_for("admin"))

@app.route("/admin/ajouter_user", methods=["POST"])
@login_requis
@admin_requis
def ajouter_user():
    login = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "utilisateur").strip()
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip()
    if login and password and nom and email:
        ajouter_utilisateur(login, password, role, nom, email)
    return redirect(url_for("admin"))

@app.route("/admin/supprimer_user/<username>")
@login_requis
@admin_requis
def supprimer_user(username):
    supprimer_utilisateur(username)
    return redirect(url_for("admin"))

@app.route("/admin/backup")
@login_requis
@admin_requis
def backup():
    faire_backup()
    return redirect(url_for("admin"))

@app.route("/admin/reinitialiser")
@login_requis
@admin_requis
def reinitialiser():
    import importlib
    import setup_db as sdb
    importlib.reload(sdb)
    sdb.creer_produits()
    log_info("Base reinitialise !")
    return redirect(url_for("admin"))

@app.route("/admin/supprimer_commandes")
@login_requis
@admin_requis
def supprimer_commandes():
    db = get_db()
    if db is not None:
        result = db.commandes.delete_many({})
        log_info(str(result.deleted_count) + " commandes supprimees !")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    demarrer_backup_automatique(intervalle_heures=24)
    log_info("Application Flask demarree !")
    app.run(debug=True, host="0.0.0.0", port=5000)

