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
        {"nom": "Mangues Kent", "categorie": "Fruits", "prix": 1500, "stock": 200,
         "producteur": "Verger de Casamance", "image": "🥭",
         "photo": "https://images.pexels.com/photos/918643/pexels-photo-918643.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Ziguinchor", "bio": True}},

        {"nom": "Bissap Seche", "categorie": "Fruits", "prix": 2500, "stock": 150,
         "producteur": "Cooperative Louga", "image": "🌺",
         "photo": "https://images.pexels.com/photos/5765/flower-red-background-hibiscus.jpg?w=300",
         "unite": "kg", "attributs": {"origine": "Louga", "bio": True}},

        {"nom": "Ditakh", "categorie": "Fruits", "prix": 2000, "stock": 80,
         "producteur": "Groupement Fatick", "image": "🍈",
         "photo": "https://images.pexels.com/photos/1132047/pexels-photo-1132047.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Fatick", "bio": True}},

        {"nom": "Tamarin", "categorie": "Fruits", "prix": 1000, "stock": 3,
         "producteur": "Marche Thies", "image": "🫘",
         "photo": "https://images.pexels.com/photos/4110251/pexels-photo-4110251.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Thies", "bio": False}},

        {"nom": "Gombo Frais", "categorie": "Legumes", "prix": 800, "stock": 120,
         "producteur": "Maraichage Pikine", "image": "🫛",
         "photo": "https://images.pexels.com/photos/6157049/pexels-photo-6157049.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Dakar", "bio": False}},

        {"nom": "Oignons Violets", "categorie": "Legumes", "prix": 600, "stock": 300,
         "producteur": "Cooperative Potou", "image": "🧅",
         "photo": "https://images.pexels.com/photos/4197447/pexels-photo-4197447.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Saint-Louis", "bio": False}},

        {"nom": "Aubergine Africaine", "categorie": "Legumes", "prix": 700, "stock": 90,
         "producteur": "Maraichage Kaolack", "image": "🍆",
         "photo": "https://images.pexels.com/photos/5639/food-vegetables-eggplant-purple.jpg?w=300",
         "unite": "kg", "attributs": {"origine": "Kaolack", "bio": True}},

        {"nom": "Piment Demon", "categorie": "Legumes", "prix": 1200, "stock": 2,
         "producteur": "Cooperative Ziguinchor", "image": "🌶️",
         "photo": "https://images.pexels.com/photos/870894/pexels-photo-870894.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Ziguinchor", "bio": True}},

        {"nom": "Mil Local", "categorie": "Cereales", "prix": 500, "stock": 500,
         "producteur": "GAEC Diourbel", "image": "🌾",
         "photo": "https://images.pexels.com/photos/326082/pexels-photo-326082.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Diourbel", "bio": True}},

        {"nom": "Riz Broken", "categorie": "Cereales", "prix": 450, "stock": 400,
         "producteur": "Riziculture Saint-Louis", "image": "🍚",
         "photo": "https://images.pexels.com/photos/7421235/pexels-photo-7421235.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Saint-Louis", "bio": False}},

        {"nom": "Mais Local", "categorie": "Cereales", "prix": 400, "stock": 4,
         "producteur": "Cooperative Tambacounda", "image": "🌽",
         "photo": "https://images.pexels.com/photos/547263/pexels-photo-547263.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Tambacounda", "bio": True}},

        {"nom": "Huile d'Arachide", "categorie": "Huiles", "prix": 3500, "stock": 60,
         "producteur": "Huilerie Kaolack", "image": "🫙",
         "photo": "https://images.pexels.com/photos/4033158/pexels-photo-4033158.jpeg?w=300",
         "unite": "litre", "attributs": {"origine": "Kaolack", "bio": True}},

        {"nom": "Huile de Palme Rouge", "categorie": "Huiles", "prix": 2800, "stock": 2,
         "producteur": "Cooperative Kolda", "image": "🫙",
         "photo": "https://images.pexels.com/photos/33783/olive-oil-salad-dressing-cooking-olive.jpg?w=300",
         "unite": "litre", "attributs": {"origine": "Kolda", "bio": True}},

        {"nom": "Thiof Seche", "categorie": "Poissons", "prix": 8000, "stock": 30,
         "producteur": "Pecheurs Kayar", "image": "🐟",
         "photo": "https://images.pexels.com/photos/1148358/pexels-photo-1148358.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Kayar"}},

        {"nom": "Yeet Mollusque", "categorie": "Poissons", "prix": 5000, "stock": 25,
         "producteur": "Pecheurs Mbour", "image": "🦪",
         "photo": "https://images.pexels.com/photos/3535383/pexels-photo-3535383.jpeg?w=300",
         "unite": "kg", "attributs": {"origine": "Mbour"}},
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
