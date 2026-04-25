import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB

def get_db():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]

def creer_produits():
    db = get_db()
    db.produits.drop()
    produits = [
        {"nom": "Mangues Kent", "categorie": "Fruits", "prix": 1500, "stock": 200, "producteur": "Verger de Casamance", "image": "🥭", "unite": "kg", "attributs": {"origine": "Ziguinchor", "bio": True}},
        {"nom": "Bissap Seche", "categorie": "Fruits", "prix": 2500, "stock": 150, "producteur": "Cooperative Louga", "image": "🌺", "unite": "kg", "attributs": {"origine": "Louga", "bio": True}},
        {"nom": "Ditakh", "categorie": "Fruits", "prix": 2000, "stock": 80, "producteur": "Groupement Fatick", "image": "🍈", "unite": "kg", "attributs": {"origine": "Fatick", "bio": True}},
        {"nom": "Tamarin", "categorie": "Fruits", "prix": 1000, "stock": 3, "producteur": "Marche Thies", "image": "🫘", "unite": "kg", "attributs": {"origine": "Thies", "bio": False}},
        {"nom": "Gombo Frais", "categorie": "Legumes", "prix": 800, "stock": 120, "producteur": "Maraichage Pikine", "image": "🫛", "unite": "kg", "attributs": {"origine": "Dakar", "bio": False}},
        {"nom": "Oignons Violets", "categorie": "Legumes", "prix": 600, "stock": 300, "producteur": "Cooperative Potou", "image": "🧅", "unite": "kg", "attributs": {"origine": "Saint-Louis", "bio": False}},
        {"nom": "Aubergine Africaine", "categorie": "Legumes", "prix": 700, "stock": 90, "producteur": "Maraichage Kaolack", "image": "🍆", "unite": "kg", "attributs": {"origine": "Kaolack", "bio": True}},
        {"nom": "Piment Demon", "categorie": "Legumes", "prix": 1200, "stock": 2, "producteur": "Cooperative Ziguinchor", "image": "🌶️", "unite": "kg", "attributs": {"origine": "Ziguinchor", "bio": True}},
        {"nom": "Mil Local", "categorie": "Cereales", "prix": 500, "stock": 500, "producteur": "GAEC Diourbel", "image": "🌾", "unite": "kg", "attributs": {"origine": "Diourbel", "bio": True}},
        {"nom": "Riz Broken", "categorie": "Cereales", "prix": 450, "stock": 400, "producteur": "Riziculture Saint-Louis", "image": "🍚", "unite": "kg", "attributs": {"origine": "Saint-Louis", "bio": False}},
        {"nom": "Mais Local", "categorie": "Cereales", "prix": 400, "stock": 4, "producteur": "Cooperative Tambacounda", "image": "🌽", "unite": "kg", "attributs": {"origine": "Tambacounda", "bio": True}},
        {"nom": "Huile d'Arachide", "categorie": "Huiles", "prix": 3500, "stock": 60, "producteur": "Huilerie Kaolack", "image": "🫙", "unite": "litre", "attributs": {"origine": "Kaolack", "bio": True}},
        {"nom": "Huile de Palme Rouge", "categorie": "Huiles", "prix": 2800, "stock": 2, "producteur": "Cooperative Kolda", "image": "🫙", "unite": "litre", "attributs": {"origine": "Kolda", "bio": True}},
        {"nom": "Thiof Seche", "categorie": "Poissons", "prix": 8000, "stock": 30, "producteur": "Pecheurs Kayar", "image": "🐟", "unite": "kg", "attributs": {"origine": "Kayar"}},
        {"nom": "Yeet Mollusque", "categorie": "Poissons", "prix": 5000, "stock": 25, "producteur": "Pecheurs Mbour", "image": "🦪", "unite": "kg", "attributs": {"origine": "Mbour"}},
    ]
    result = db.produits.insert_many(produits)
    print("OK " + str(len(result.inserted_ids)) + " produits inseres !")
    return result.inserted_ids

def creer_index():
    db = get_db()
    db.produits.create_index("categorie")
    db.produits.create_index("stock")
    db.commandes.create_index("client")
    db.commandes.create_index("date")
    db.commandes.create_index("statut")
    print("OK Index crees !")

if __name__ == "__main__":
    print("Initialisation Terroir Local Senegal...")
    creer_produits()
    creer_index()
    print("Base de donnees prete !")
