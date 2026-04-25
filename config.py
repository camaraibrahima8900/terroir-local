import os

# Chemin du projet (automatique)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# MONGODB
MONGO_URI = "mongodb+srv://camaraibrahima8900:Pibcmr8900@cluster0.5r4lftj.mongodb.net/terroir_local?appName=Cluster0"
MONGO_AUTH_SOURCE = "admin"
MONGO_DB = "terroir_local"

# LIVRAISON
FRAIS_LIVRAISON = {"normal": 500, "express": 2000}

# STOCK
SEUIL_RUPTURE = 5
SEUIL_STOCK_BAS = 20

# FICHIERS
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOG_FILE = os.path.join(BASE_DIR, "logs", "terroir.log")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# APPLICATION
DEVISE = "FCFA"
APP_NOM = "Terroir Local Senegal"
VERSION = "1.0.0"
