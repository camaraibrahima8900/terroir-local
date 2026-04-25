"""
requetes.py - Requêtes MongoDB pour la coopérative Terroir Local
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import pprint

def get_db():
    client = MongoClient("mongodb://admin:motdepasse@localhost:27017/", authSource="admin")
    return client["terroir_local"]

def produits_rupture_stock(seuil=5):
    db = get_db()
    produits = list(db.produits.find(
        {"stock": {"$lt": seuil}},
        {"nom": 1, "categorie": 1, "stock": 1, "producteur": 1, "_id": 0}
    ).sort("stock", 1))
    
    print(f"\n⚠️  PRODUITS EN RUPTURE DE STOCK (stock < {seuil})")
    print("─" * 55)
    if not produits:
        print("   Aucun produit en rupture de stock.")
    for p in produits:
        print(f"  🔴 {p['nom']:<30} Stock: {p['stock']:>3}  [{p['categorie']}]")
    return produits

def chiffre_affaires_par_categorie():
    db = get_db()
    pipeline = [
        {"$unwind": "$articles"},
        {"$lookup": {"from": "produits", "localField": "articles.produit_id", "foreignField": "_id", "as": "produit_info"}},
        {"$unwind": "$produit_info"},
        {"$group": {
            "_id": "$produit_info.categorie",
            "chiffre_affaires": {"$sum": {"$multiply": ["$articles.quantite", "$articles.prix_unitaire"]}},
            "nb_commandes": {"$sum": 1},
            "quantite_vendue": {"$sum": "$articles.quantite"}
        }},
        {"$sort": {"chiffre_affaires": -1}}
    ]
    
    resultats = list(db.commandes.aggregate(pipeline))
    print("\n💰 CHIFFRE D'AFFAIRES PAR CATÉGORIE")
    print("─" * 55)
    total_general = 0
    for r in resultats:
        ca = r["chiffre_affaires"]
        total_general += ca
        print(f"  📦 {r['_id']:<20} CA: {ca:>8.2f}€  |  {r['nb_commandes']} ventes  |  {r['quantite_vendue']} unités")
    print(f"\n  {'TOTAL GÉNÉRAL':<20}    {total_general:>8.2f}€")
    return resultats

def historique_client(email_client):
    db = get_db()
    commandes = list(db.commandes.find(
        {"client.email": email_client},
        {"_id": 0}
    ).sort("date", -1))
    
    print(f"\n📋 HISTORIQUE COMMANDES - {email_client}")
    print("─" * 55)
    if not commandes:
        print("   Aucune commande trouvée pour ce client.")
        return []
    
    for i, cmd in enumerate(commandes, 1):
        print(f"\n  Commande #{i} | {cmd['date'].strftime('%d/%m/%Y %H:%M')} | Statut: {cmd['statut'].upper()}")
        for article in cmd["articles"]:
            print(f"    • {article['nom_produit']:<30} x{article['quantite']}  @ {article['prix_unitaire']:.2f}€")
        print(f"    {'─' * 46}")
        print(f"    TOTAL: {cmd['total']:.2f}€")
    
    total_depenses = sum(c["total"] for c in commandes)
    print(f"\n  Total dépensé: {total_depenses:.2f}€ sur {len(commandes)} commandes")
    return commandes

def decrementer_stock(produit_id, quantite):
    db = get_db()
    from bson import ObjectId
    if isinstance(produit_id, str):
        produit_id = ObjectId(produit_id)
    
    produit = db.produits.find_one({"_id": produit_id})
    if not produit:
        print(f"❌ Produit introuvable")
        return False
    
    if produit["stock"] < quantite:
        print(f"❌ Stock insuffisant: {produit['stock']} disponibles, {quantite} demandés")
        return False
    
    result = db.produits.update_one(
        {"_id": produit_id, "stock": {"$gte": quantite}},
        {"$inc": {"stock": -quantite}}
    )
    
    if result.modified_count > 0:
        nouveau_stock = produit["stock"] - quantite
        print(f"✅ Stock mis à jour: {produit['nom']} → {produit['stock']} → {nouveau_stock}")
        return True
    return False

def produits_plus_vendus(limit=5):
    db = get_db()
    pipeline = [
        {"$unwind": "$articles"},
        {"$group": {
            "_id": "$articles.produit_id",
            "nom": {"$first": "$articles.nom_produit"},
            "quantite_totale": {"$sum": "$articles.quantite"},
            "revenus": {"$sum": {"$multiply": ["$articles.quantite", "$articles.prix_unitaire"]}},
            "nb_commandes": {"$sum": 1}
        }},
        {"$sort": {"quantite_totale": -1}},
        {"$limit": limit}
    ]
    
    resultats = list(db.commandes.aggregate(pipeline))
    print(f"\n🏆 TOP {limit} PRODUITS LES PLUS VENDUS")
    print("─" * 55)
    for i, r in enumerate(resultats, 1):
        print(f"  {i}. {r['nom']:<30} {r['quantite_totale']:>4} unités  ({r['revenus']:.2f}€)")
    return resultats

def statistiques_globales():
    db = get_db()
    nb_produits = db.produits.count_documents({})
    nb_commandes = db.commandes.count_documents({})
    nb_ruptures = db.produits.count_documents({"stock": {"$lt": 5}})
    
    agg = list(db.commandes.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "moyenne": {"$avg": "$total"}}}
    ]))
    
    ca_total = agg[0]["total"] if agg else 0
    panier_moyen = agg[0]["moyenne"] if agg else 0
    
    print("\n📊 STATISTIQUES GLOBALES")
    print("─" * 55)
    print(f"  Produits en catalogue : {nb_produits}")
    print(f"  Commandes totales     : {nb_commandes}")
    print(f"  Produits en rupture   : {nb_ruptures}")
    print(f"  CA total              : {ca_total:.2f}€")
    print(f"  Panier moyen          : {panier_moyen:.2f}€")
    return {"nb_produits": nb_produits, "nb_commandes": nb_commandes, "ca_total": ca_total}

if __name__ == "__main__":
    print("=" * 55)
    print("   🌿 TERROIR LOCAL - REQUÊTES MONGODB")
    print("=" * 55)
    
    produits_rupture_stock(seuil=5)
    chiffre_affaires_par_categorie()
    historique_client("marie.dubois@email.fr")
    produits_plus_vendus(limit=5)
    statistiques_globales()
