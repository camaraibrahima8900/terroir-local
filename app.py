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

CODES_PROMO = {
    "TERROIR10": 10,
    "SENEGAL20": 20,
    "BIENVENUE15": 15,
    "KOUSSANAR5": 5,
}

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
        client = MongoClient(MONGO_URI, authSource=MONGO_AUTH_SOURCE, serverSelectionTimeoutMS=10000)
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
    prix_max = request.args.get("prix_max", "")
    if categorie != "Toutes":
        filtre["categorie"] = categorie
    if search:
        filtre["nom"] = {"$regex": search, "$options": "i"}
    prix_min = request.args.get("prix_min", "")
    producteur = request.args.get("producteur", "")
    tri = request.args.get("tri", "nom")
    if prix_min and prix_max:
        filtre["prix"] = {"$gte": int(prix_min), "$lte": int(prix_max)}
    elif prix_min:
        filtre["prix"] = {"$gte": int(prix_min)}
    elif prix_max:
        filtre["prix"] = {"$lte": int(prix_max)}
    if producteur:
        filtre["producteur"] = {"$regex": producteur, "$options": "i"}
    tri_map = {
        "nom": ("nom", 1),
        "prix_asc": ("prix", 1),
        "prix_desc": ("prix", -1),
        "stock": ("stock", -1),
        "categorie": ("categorie", 1)
    }
    tri_field, tri_order = tri_map.get(tri, ("nom", 1))
    page = int(request.args.get("page", 1))
    par_page = 9
    total_produits = db.produits.count_documents(filtre)
    total_pages = max(1, (total_produits + par_page - 1) // par_page)
    page = max(1, min(page, total_pages))
    produits = list(db.produits.find(filtre).sort(tri_field, tri_order).skip((page-1)*par_page).limit(par_page))
    # Calculer prix_final selon promo stockee en DB
    for p in produits:
        p["_id"] = str(p["_id"])
        promo_produit = p.get("promo", 0)
        if promo_produit > 0:
            p["prix_final"] = int(p["prix"] * (1 - promo_produit / 100))
        else:
            p["prix_final"] = p["prix"]
    for p in produits:
        p["_id"] = str(p["_id"])
        p["prix_final"] = int(p["prix"] * (1 - promo / 100))
        p["promo"] = promo
    panier = session.get("panier", [])
    total = sum(i["quantite"] * i["prix_final"] for i in panier)
    return render_template("boutique.html",
        produits=produits, categories=CATEGORIES, regions=REGIONS,
        categorie=categorie, search=search, promo=promo,
        prix_max=prix_max, prix_min=prix_min,
        producteur=producteur, tri=tri,
        page=page, total_pages=total_pages, total_produits=total_produits,
        panier=panier, total=total, role=session.get("role"),
        username=session.get("username"), devise=DEVISE)

@app.route("/ajouter_panier_ajax", methods=["POST"])
@login_requis
def ajouter_panier_ajax():
    produit_id = request.form.get("produit_id")
    quantite = int(request.form.get("quantite", 1))
    promo = int(request.form.get("promo", 0))
    db = get_db()
    if db is None:
        return jsonify({"success": False, "message": "Erreur MongoDB"})
    produit = db.produits.find_one({"_id": ObjectId(produit_id)})
    if not produit or produit["stock"] < quantite:
        return jsonify({"success": False, "message": "Stock insuffisant"})
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
    total = sum(i["quantite"] * i["prix_final"] for i in panier)
    return jsonify({
        "success": True,
        "nom": produit["nom"],
        "nb": len(panier),
        "total": total,
        "items": panier
    })

@app.route("/panier_data")
@login_requis
def panier_data():
    panier = session.get("panier", [])
    total = sum(i["quantite"] * i["prix_final"] for i in panier)
    return jsonify({
        "nb": len(panier),
        "total": total,
        "items": panier
    })

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
    referer = request.referrer or url_for("boutique")
    return redirect(referer)

@app.route("/vider_panier_ajax")
@login_requis
def vider_panier_ajax():
    session["panier"] = []
    session.modified = True
    return jsonify({"success": True})

@app.route("/retirer_panier_ajax/<int:index>")
@login_requis
def retirer_panier_ajax(index):
    panier = session.get("panier", [])
    if 0 <= index < len(panier):
        panier.pop(index)
    session["panier"] = panier
    session.modified = True
    total = sum(i["quantite"] * i["prix_final"] for i in panier)
    return jsonify({"success": True, "nb": len(panier), "total": total, "items": panier})

@app.route("/suivi/update_ajax/<commande_id>", methods=["POST"])
@login_requis
@admin_requis
def update_statut_ajax(commande_id):
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    nouveau_statut = request.form.get("statut")
    db.commandes.update_one(
        {"_id": ObjectId(commande_id)},
        {"$set": {"statut": nouveau_statut}}
    )
    log_info("Statut AJAX mis a jour : " + commande_id + " -> " + nouveau_statut)
    return jsonify({"success": True, "statut": nouveau_statut})

@app.route("/noter_ajax/<produit_id>", methods=["POST"])
@login_requis
def noter_produit_ajax(produit_id):
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    note = int(request.form.get("note", 5))
    db.produits.update_one(
        {"_id": ObjectId(produit_id)},
        {"$push": {"notes": note}, "$set": {"note_moyenne": note}}
    )
    return jsonify({"success": True, "note": note})

@app.route("/vider_panier")
@login_requis
def vider_panier():
    session["panier"] = []
    session.modified = True
    referer = request.referrer or url_for("boutique")
    return redirect(referer)

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
    frais_custom = request.form.get("frais_custom", "")
    if frais_custom and str(frais_custom).isdigit():
        frais = int(frais_custom)
    else:
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
    try:
        for item in panier:
            db.produits.update_one(
                {"_id": ObjectId(item["produit_id"])},
                {"$inc": {"stock": -item["quantite"]}}
            )
        db.commandes.insert_one(commande)
        log_info("Commande - " + client["nom"] + " - " + str(total_avec_frais) + " FCFA")
    except Exception as e:
        log_erreur("Erreur commande: " + str(e))
    session["panier"] = []
    session.modified = True
    return render_template("confirmation.html",
        client=client, region=region, type_livraison=type_livraison,
        frais=frais, sous_total=sous_total, reduction=reduction,
        total=total_avec_frais, devise=DEVISE,
        role=session.get("role"), username=session.get("username"))

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
    role_actuel = session.get("role", "")
    users_brut = lister_utilisateurs()
    users = users_brut
    backups = lister_backups()
    return render_template("admin.html",
        produits=produits, users=users, backups=backups,
        categories=CATEGORIES, regions=REGIONS,
        role=role_actuel, username=session.get("username"))

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
    photo = request.form.get("photo", "").strip()
    photo_base64 = request.form.get("photo_base64", "").strip()
    if photo_base64:
        photo = photo_base64
    if nom and categorie and prix and stock and producteur:
        db.produits.insert_one({
            "nom": nom, "categorie": categorie, "prix": prix,
            "stock": stock, "unite": unite, "producteur": producteur,
            "image": image, "photo": photo,
            "ajoute_par": session.get("username"),
            "attributs": {"origine": origine, "bio": False}
        })
        log_info("Produit ajoute : " + nom)
    return redirect(url_for("admin"))

@app.route("/admin/maj_image_ajax", methods=["POST"])
@login_requis
@admin_requis
def maj_image_ajax():
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    produit_id = request.form.get("produit_id")
    photo = request.form.get("photo", "")
    db.produits.update_one(
        {"_id": ObjectId(produit_id)},
        {"$set": {"photo": photo}}
    )
    log_info("Image produit mise a jour : " + produit_id)
    return jsonify({"success": True})

@app.route("/admin/supprimer_produit_ajax/<produit_id>")
@login_requis
@admin_requis
def supprimer_produit_ajax(produit_id):
    db = get_db()
    if db is not None:
        username = session.get("username")
        if username == "admin":
            db.produits.delete_one({"_id": ObjectId(produit_id)})
        else:
            db.produits.delete_one({"_id": ObjectId(produit_id), "ajoute_par": username})
        log_info("Produit supprime AJAX : " + produit_id)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/admin/bloquer_user_ajax/<username_cible>")
@login_requis
@admin_requis
def bloquer_user_ajax(username_cible):
    if session.get("username") != "admin":
        return jsonify({"success": False, "message": "Non autorise"})
    from auth import charger_users, sauvegarder_users
    users = charger_users()
    if username_cible not in users or username_cible == "admin":
        return jsonify({"success": False, "message": "Utilisateur introuvable"})
    current = users[username_cible].get("bloque", False)
    users[username_cible]["bloque"] = not current
    sauvegarder_users(users)
    statut = "bloque" if not current else "debloque"
    log_info(f"Utilisateur {username_cible} {statut} par admin")
    return jsonify({"success": True, "bloque": not current, "statut": statut})

@app.route("/admin/supprimer_user_ajax/<username_cible>")
@login_requis
@admin_requis
def supprimer_user_ajax(username_cible):
    current = session.get("username")
    if username_cible == "admin":
        return jsonify({"success": False, "message": "Impossible de supprimer admin"})
    if current == "admin":
        supprimer_utilisateur(username_cible)
        return jsonify({"success": True})
    else:
        users = lister_utilisateurs()
        user_data = next((u for u in users if u[0] == username_cible), None)
        if user_data and len(user_data) > 4 and user_data[4] == current:
            supprimer_utilisateur(username_cible)
            return jsonify({"success": True})
    return jsonify({"success": False, "message": "Non autorise"})

@app.route("/admin/maj_stock_ajax", methods=["POST"])
@login_requis
@admin_requis
def maj_stock_ajax():
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    produit_id = request.form.get("produit_id")
    stock = int(request.form.get("stock", 0))
    db.produits.update_one({"_id": ObjectId(produit_id)}, {"$set": {"stock": stock}})
    log_info("Stock AJAX mis a jour : " + str(stock))
    return jsonify({"success": True, "stock": stock})

@app.route("/admin/maj_promo_ajax", methods=["POST"])
@login_requis
@admin_requis
def maj_promo_ajax():
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    produit_id = request.form.get("produit_id")
    promo = int(request.form.get("promo", 0))
    produit = db.produits.find_one({"_id": ObjectId(produit_id)})
    if not produit:
        return jsonify({"success": False})
    prix = produit["prix"]
    prix_final = int(prix * (1 - promo / 100))
    db.produits.update_one(
        {"_id": ObjectId(produit_id)},
        {"$set": {"promo": promo, "prix_final": prix_final}}
    )
    log_info("Promo mis a jour : " + str(promo) + "% prix_final=" + str(prix_final))
    return jsonify({"success": True, "promo": promo, "prix": prix, "prix_final": prix_final})

@app.route("/admin/maj_prix_ajax", methods=["POST"])
@login_requis
@admin_requis
def maj_prix_ajax():
    db = get_db()
    if db is None:
        return jsonify({"success": False})
    produit_id = request.form.get("produit_id")
    prix = int(request.form.get("prix", 0))
    db.produits.update_one({"_id": ObjectId(produit_id)}, {"$set": {"prix": prix}})
    log_info("Prix AJAX mis a jour : " + str(prix))
    return jsonify({"success": True, "prix": prix})

@app.route("/admin/supprimer_produit/<produit_id>")
@login_requis
@admin_requis
def supprimer_produit(produit_id):
    db = get_db()
    if db is not None:
        username = session.get("username")
        if username == "admin":
            db.produits.delete_one({"_id": ObjectId(produit_id)})
        else:
            db.produits.delete_one({"_id": ObjectId(produit_id), "ajoute_par": username})
        log_info("Produit supprime : " + produit_id + " par " + username)
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

@app.route("/admin/ajouter_user_ajax", methods=["POST"])
@login_requis
@admin_requis
def ajouter_user_ajax():
    login = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "utilisateur").strip()
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip()
    telephone = request.form.get("telephone", "").strip()
    lieu = request.form.get("lieu", "").strip()
    if login and password and nom and email:
        try:
            result = ajouter_utilisateur(login, password, role, nom, email,
                                        session.get("username"), telephone, lieu)
            if isinstance(result, tuple):
                success, msg = result
            else:
                success, msg = True, "OK"
            if success:
                log_info("Utilisateur AJAX cree : " + login)
                return jsonify({
                    "success": True,
                    "login": login, "nom": nom, "email": email,
                    "role": role, "telephone": telephone, "lieu": lieu
                })
            else:
                return jsonify({"success": False, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    return jsonify({"success": False, "message": "Champs obligatoires manquants"})

@app.route("/admin/ajouter_user", methods=["POST"])
@login_requis
@admin_requis
def ajouter_user():
    login = request.form.get("login", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "utilisateur").strip()
    nom = request.form.get("nom", "").strip()
    email = request.form.get("email", "").strip()
    telephone = request.form.get("telephone", "").strip()
    lieu = request.form.get("lieu", "").strip()
    if login and password and nom and email:
        ajouter_utilisateur(login, password, role, nom, email,
                           session.get("username"), telephone, lieu)
    return redirect(url_for("admin"))

@app.route("/admin/supprimer_user/<username>")
@login_requis
@admin_requis
def supprimer_user(username):
    current = session.get("username")
    # Seul admin peut tout supprimer
    # Un admin non-root ne peut supprimer que les users qu il a crees
    if username == "admin":
        log_info("Tentative suppression admin refusee par " + current)
        return redirect(url_for("admin"))
    if current == "admin":
        supprimer_utilisateur(username)
        log_info("User supprime par admin : " + username)
    else:
        # Verifier si cet user a ete cree par cet admin
        users = lister_utilisateurs()
        user_data = next((u for u in users if u[0] == username), None)
        if user_data and len(user_data) > 4 and user_data[4] == current:
            supprimer_utilisateur(username)
            log_info("User supprime par " + current + " : " + username)
        else:
            log_info("Suppression refusee : " + current + " ne peut pas supprimer " + username)
    return redirect(url_for("admin"))

@app.route("/admin/backup_ajax")
@login_requis
@admin_requis
def backup_ajax():
    try:
        faire_backup()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/admin/reinitialiser_ajax")
@login_requis
@admin_requis
def reinitialiser_ajax():
    try:
        import importlib
        import setup_db as sdb
        importlib.reload(sdb)
        sdb.creer_produits()
        log_info("Base reinitialise AJAX!")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/admin/supprimer_commandes_ajax")
@login_requis
@admin_requis
def supprimer_commandes_ajax():
    try:
        db = get_db()
        if db is not None:
            result = db.commandes.delete_many({})
            log_info(str(result.deleted_count) + " commandes supprimees AJAX!")
            return jsonify({"success": True, "nb": result.deleted_count})
        return jsonify({"success": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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

@app.route("/suivi")
@login_requis
def suivi():
    db = get_db()
    if db is None:
        return render_template("erreur.html", message="Connexion MongoDB echouee !")
    email = session.get("username")
    commandes = list(db.commandes.find({}).sort("date", -1).limit(20))
    for c in commandes:
        c["_id"] = str(c["_id"])
        c["date_str"] = c["date"].strftime("%d/%m/%Y %H:%M")
    return render_template("suivi.html",
        commandes=commandes,
        role=session.get("role"),
        username=session.get("username"))

@app.route("/suivi/update/<commande_id>", methods=["POST"])
@login_requis
@admin_requis
def update_statut(commande_id):
    db = get_db()
    if db is None:
        return redirect(url_for("suivi"))
    from bson import ObjectId
    nouveau_statut = request.form.get("statut")
    db.commandes.update_one(
        {"_id": ObjectId(commande_id)},
        {"$set": {"statut": nouveau_statut}}
    )
    log_info("Statut commande mis a jour : " + commande_id + " -> " + nouveau_statut)
    return redirect(url_for("suivi"))

@app.route("/facture/<commande_id>")
@login_requis
def facture(commande_id):
    db = get_db()
    if db is None:
        return render_template("erreur.html", message="Connexion MongoDB echouee !")
    from bson import ObjectId
    try:
        cmd = db.commandes.find_one({"_id": ObjectId(commande_id)})
        if not cmd:
            return render_template("erreur.html", message="Commande introuvable !")
        cmd["_id"] = str(cmd["_id"])
        cmd["date_str"] = cmd["date"].strftime("%d/%m/%Y %H:%M")
        return render_template("facture.html",
            cmd=cmd, role=session.get("role"),
            username=session.get("username"))
    except:
        return render_template("erreur.html", message="Commande introuvable !")

@app.route("/noter/<produit_id>", methods=["POST"])
@login_requis
def noter_produit(produit_id):
    db = get_db()
    if db is None:
        return redirect(url_for("boutique"))
    from bson import ObjectId
    note = int(request.form.get("note", 5))
    db.produits.update_one(
        {"_id": ObjectId(produit_id)},
        {"$push": {"notes": note}, "$set": {"note_moyenne": note}}
    )
    log_info("Produit note : " + produit_id + " -> " + str(note))
    return redirect(url_for("boutique"))

@app.route("/historique")
@login_requis
def historique():
    db = get_db()
    if db is None:
        return render_template("erreur.html", message="Connexion MongoDB echouee !")
    email = request.args.get("email", "")
    commandes = []
    total_depense = 0
    if email:
        commandes = list(db.commandes.find({"client.email": email}).sort("date", -1))
        for c in commandes:
            c["_id"] = str(c["_id"])
            c["date_str"] = c["date"].strftime("%d/%m/%Y %H:%M")
        total_depense = sum(c["total"] for c in commandes)
    clients = list(db.commandes.aggregate([
        {"$group": {"_id": "$client.email", "nom": {"$first": "$client.nom"}, "nb": {"$sum": 1}, "total": {"$sum": "$total"}}},
        {"$sort": {"total": -1}}
    ]))
    return render_template("historique.html",
        commandes=commandes, clients=clients,
        email=email, total_depense=total_depense,
        role=session.get("role"), username=session.get("username"))

@app.route("/export_commandes")
@login_requis
@admin_requis
def export_commandes():
    import csv
    import io
    db = get_db()
    if db is None:
        return redirect(url_for("admin"))
    commandes = list(db.commandes.find({}).sort("date", -1))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Client", "Telephone", "Ville", "Region", "Livraison", "Total FCFA", "Statut"])
    for c in commandes:
        writer.writerow([
            c["date"].strftime("%d/%m/%Y %H:%M"),
            c["client"]["nom"],
            c["client"]["telephone"],
            c["client"].get("ville", ""),
            c["livraison"].get("region", ""),
            c["livraison"].get("type", "normal"),
            c["total"],
            c.get("statut", "en_attente")
        ])
    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=commandes_terroir_local.csv"}
    )

@app.route("/verifier_promo", methods=["POST"])
@login_requis
def verifier_promo():
    code = request.form.get("code", "").upper().strip()
    if code in CODES_PROMO:
        reduction = CODES_PROMO[code]
        return jsonify({"success": True, "reduction": reduction, "message": f"Code valide ! -{reduction}% sur votre commande !"})
    return jsonify({"success": False, "message": "Code promo invalide !"})

@app.route("/ajouter_avis/<produit_id>", methods=["POST"])
@login_requis
def ajouter_avis(produit_id):
    db = get_db()
    if db is None:
        return redirect(url_for("boutique"))
    commentaire = request.form.get("commentaire", "").strip()
    note = int(request.form.get("note", 5))
    if commentaire:
        db.produits.update_one(
            {"_id": ObjectId(produit_id)},
            {"$push": {"avis": {
                "auteur": session.get("username"),
                "commentaire": commentaire,
                "note": note,
                "date": datetime.now().strftime("%d/%m/%Y")
            }}, "$set": {"note_moyenne": note}}
        )
        log_info("Avis ajoute sur produit " + produit_id)
    referer = request.referrer or url_for("boutique")
    return redirect(referer)

@app.route("/profil", methods=["GET", "POST"])
@login_requis
def profil():
    if request.method == "POST":
        action = request.form.get("action")
        username = session.get("username")
        if action == "changer_mdp":
            ancien = request.form.get("ancien_mdp", "")
            nouveau = request.form.get("nouveau_mdp", "")
            if authentifier(username, ancien) and nouveau:
                from auth import charger_users, sauvegarder_users
                import bcrypt
                users = charger_users()
                users[username]["password"] = bcrypt.hashpw(nouveau.encode(), bcrypt.gensalt()).decode()
                sauvegarder_users(users)
                from auth import charger_users
                users_data = charger_users()
                ud = users_data.get(username, {})
                return render_template("profil.html",
                    msg_success="Mot de passe change avec succes !",
                    user_data=ud, role=session.get("role"), username=username)
            else:
                from auth import charger_users
                users_data = charger_users()
                ud = users_data.get(username, {})
                return render_template("profil.html",
                    msg_error="Ancien mot de passe incorrect !",
                    user_data=ud, role=session.get("role"), username=username)
        elif action == "toggle_telephone":
            telephone_public = request.form.get("telephone_public") == "on"
            from auth import charger_users, sauvegarder_users
            users_t = charger_users()
            if username in users_t:
                users_t[username]["telephone_public"] = telephone_public
                sauvegarder_users(users_t)
            ud = users_t.get(username, {})
            return render_template("profil.html",
                user_data=ud,
                msg_success="Preference mise a jour !",
                role=session.get("role"), username=username)
        elif action == "changer_photo":
            photo_data = request.form.get("photo_base64", "").strip()
            from auth import charger_users, sauvegarder_users
            users = charger_users()
            if username in users and photo_data:
                users[username]["photo"] = photo_data
                sauvegarder_users(users)
            user_data = users.get(username, {})
            return render_template("profil.html",
                user_data=user_data,
                msg_success="Photo mise a jour !",
                role=session.get("role"), username=username)
        elif action == "changer_avatar":
            avatar = request.form.get("avatar", "👤")
            from auth import charger_users, sauvegarder_users
            users = charger_users()
            if username in users:
                users[username]["avatar"] = avatar
                sauvegarder_users(users)
            session["avatar"] = avatar
            return render_template("profil.html",
                msg_success="Avatar change !",
                role=session.get("role"), username=username)
    from auth import charger_users
    users = charger_users()
    username_val = session.get("username")
    user_data = users.get(username_val, {})
    return render_template("profil.html",
        user_data=user_data,
        role=session.get("role"),
        username=username_val)

@app.route("/nb_commandes_attente")
@login_requis
def nb_commandes_attente():
    db = get_db()
    if db is None:
        return jsonify({"nb": 0})
    nb = db.commandes.count_documents({"statut": "en_attente"})
    return jsonify({"nb": nb})

@app.route("/apropos")
def apropos():
    return render_template("apropos.html", role=session.get("role"), username=session.get("username"))

if __name__ == "__main__":
    demarrer_backup_automatique(intervalle_heures=24)
    log_info("Application Flask demarree !")
    app.run(debug=True, host="0.0.0.0", port=5000)

