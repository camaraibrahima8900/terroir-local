import tkinter as tk
from tkinter import ttk, messagebox
from pymongo import MongoClient
from datetime import datetime
import threading
import time
import random
import sys
import os

sys.path.insert(0, "/home/ibrahima/terroir_local")
from auth import authentifier, lister_utilisateurs, ajouter_utilisateur, supprimer_utilisateur
from logger import log_info, log_erreur, log_warning
from backup import faire_backup, demarrer_backup_automatique, lister_backups, BACKUP_DIR

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
        client = MongoClient("mongodb://admin:motdepasse@localhost:27017/",
                             authSource="admin", serverSelectionTimeoutMS=3000)
        client.server_info()
        return client["terroir_local"]
    except Exception as e:
        log_erreur("Connexion MongoDB echouee : " + str(e))
        messagebox.showerror("Erreur connexion", "Impossible de se connecter a MongoDB !\nVerifiez que Docker est lance.\n\nCommande : docker compose up -d")
        return None


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Terroir Local Senegal - Connexion")
        self.root.geometry("400x480")
        self.root.configure(bg="#f5f0e8")
        self.role = None
        self.tentatives = 0
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="Terroir Local Senegal", font=("Helvetica", 20, "bold"),
                 bg="#f5f0e8", fg="#2C5F2D").pack(pady=(40, 5))
        tk.Label(self.root, text="Plateforme Agricole Senegalaise",
                 font=("Helvetica", 11), bg="#f5f0e8", fg="#4a7c59").pack(pady=(0, 25))

        frame = tk.Frame(self.root, bg="#ffffff")
        frame.pack(padx=40, fill="x")

        tk.Label(frame, text="Nom utilisateur", bg="#ffffff",
                 font=("Helvetica", 10)).pack(anchor="w", padx=20, pady=(20, 2))
        self.entry_user = tk.Entry(frame, font=("Helvetica", 12), width=25)
        self.entry_user.pack(padx=20, ipady=6, fill="x")

        tk.Label(frame, text="Mot de passe", bg="#ffffff",
                 font=("Helvetica", 10)).pack(anchor="w", padx=20, pady=(12, 2))
        self.entry_pass = tk.Entry(frame, font=("Helvetica", 12), width=25, show="*")
        self.entry_pass.pack(padx=20, ipady=6, fill="x")
        self.entry_pass.bind("<Return>", lambda e: self.login())

        tk.Button(frame, text="Se connecter", command=self.login,
                  bg="#2C5F2D", fg="white", font=("Helvetica", 12, "bold"),
                  relief="flat", pady=8).pack(padx=20, pady=20, fill="x")

        tk.Label(self.root, text="admin / admin123  ->  Administrateur",
                 font=("Helvetica", 9), bg="#f5f0e8", fg="#4a7c59").pack()
        tk.Label(self.root, text="user / user123    ->  Utilisateur",
                 font=("Helvetica", 9), bg="#f5f0e8", fg="#2980b9").pack()

        self.label_error = tk.Label(self.root, text="",
                                     font=("Helvetica", 10), bg="#f5f0e8", fg="#c0392b")
        self.label_error.pack(pady=5)

        self.label_tentatives = tk.Label(self.root, text="",
                                          font=("Helvetica", 9), bg="#f5f0e8", fg="#e67e22")
        self.label_tentatives.pack()

    def login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            self.label_error.config(text="Remplissez tous les champs !")
            return

        if self.tentatives >= 5:
            self.label_error.config(text="Trop de tentatives ! Relancez l'application.")
            log_warning("Compte bloque apres 5 tentatives : " + username)
            return

        role = authentifier(username, password)
        if role:
            self.role = role
            self.root.destroy()
        else:
            self.tentatives += 1
            restantes = 5 - self.tentatives
            self.label_error.config(text="Identifiants incorrects !")
            self.label_tentatives.config(text=str(restantes) + " tentative(s) restante(s)")
            self.entry_pass.delete(0, "end")


class TerroirApp:
    def __init__(self, root, role):
        self.root = root
        self.role = role
        self.root.title("Terroir Local Senegal - " + role.capitalize())
        self.root.geometry("1300x800")
        self.root.configure(bg="#f5f0e8")
        self.panier = []
        self.generateur_actif = False
        log_info("Application demarree - role : " + role)
        demarrer_backup_automatique(intervalle_heures=24)
        self.build_ui()
        self.charger_produits()
        self.verifier_stock_bas()

    def build_ui(self):
        frame_header = tk.Frame(self.root, bg="#2C5F2D", height=45)
        frame_header.pack(fill="x")
        frame_header.pack_propagate(False)
        tk.Label(frame_header, text="Terroir Local Senegal",
                 font=("Helvetica", 16, "bold"), bg="#2C5F2D", fg="white").pack(side="left", padx=15)
        role_color = "#f39c12" if self.role == "administrateur" else "#3498db"
        tk.Label(frame_header, text=self.role.capitalize(),
                 font=("Helvetica", 11, "bold"), bg="#2C5F2D", fg=role_color).pack(side="right", padx=15)
        tk.Button(frame_header, text="Deconnexion", command=self.deconnexion,
                  bg="#c0392b", fg="white", relief="flat").pack(side="right", padx=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_boutique = tk.Frame(self.notebook, bg="#f5f0e8")
        self.notebook.add(self.frame_boutique, text="Boutique")

        if self.role == "administrateur":
            self.frame_stats = tk.Frame(self.notebook, bg="#f5f0e8")
            self.notebook.add(self.frame_stats, text="Statistiques")
            self.frame_admin = tk.Frame(self.notebook, bg="#f5f0e8")
            self.notebook.add(self.frame_admin, text="Administration")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.build_boutique()
        if self.role == "administrateur":
            self.build_stats()
            self.build_admin()

    def deconnexion(self):
        log_info("Deconnexion : " + self.role)
        self.root.destroy()
        main()

    def verifier_stock_bas(self):
        if self.role != "administrateur":
            return
        db = get_db()
        if not db:
            return
        ruptures = list(db.produits.find({"stock": {"$lt": 5}}))
        if ruptures:
            noms = "\n".join(["- " + p["nom"] + " (stock: " + str(p["stock"]) + ")" for p in ruptures])
            log_warning("Alerte stock bas : " + str(len(ruptures)) + " produit(s)")
            messagebox.showwarning("ALERTE STOCK BAS",
                str(len(ruptures)) + " produit(s) en rupture :\n\n" + noms + "\n\nVeuillez reapprovisionner !")

    def build_boutique(self):
        frame_top = tk.Frame(self.frame_boutique, bg="#f5f0e8")
        frame_top.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top, text="Categorie:", bg="#f5f0e8").pack(side="left")
        self.categorie_var = tk.StringVar(value="Toutes")
        ttk.Combobox(frame_top, textvariable=self.categorie_var,
                     values=["Toutes"] + CATEGORIES, width=12, state="readonly").pack(side="left", padx=4)
        self.categorie_var.trace("w", lambda *a: self.charger_produits())

        tk.Label(frame_top, text="Produit:", bg="#f5f0e8").pack(side="left", padx=(10,0))
        self.search_nom = tk.StringVar()
        tk.Entry(frame_top, textvariable=self.search_nom, width=15).pack(side="left", padx=4)
        self.search_nom.trace("w", lambda *a: self.charger_produits())

        tk.Label(frame_top, text="Promo(%):", bg="#f5f0e8").pack(side="left", padx=(10,0))
        self.promo_var = tk.IntVar(value=0)
        ttk.Combobox(frame_top, textvariable=self.promo_var,
                     values=[0,5,10,15,20,25,30], width=5, state="readonly").pack(side="left", padx=4)

        tk.Button(frame_top, text="Reinitialiser", command=self.reinitialiser_filtres,
                  bg="#95a5a6", fg="white", padx=8).pack(side="left", padx=8)

        if self.role == "administrateur":
            self.btn_gen = tk.Button(frame_top, text="Generateur OFF",
                                      command=self.toggle_generateur, bg="#c0392b", fg="white", padx=8)
            self.btn_gen.pack(side="right", padx=10)

        frame_main = tk.Frame(self.frame_boutique, bg="#f5f0e8")
        frame_main.pack(fill="both", expand=True, padx=10)

        frame_produits = tk.LabelFrame(frame_main, text="Produits disponibles",
                                        bg="#f5f0e8", font=("Helvetica", 11, "bold"))
        frame_produits.pack(side="left", fill="both", expand=True, padx=5)

        cols = ("Produit","Categorie","Prix (FCFA)","Promo","Prix final","Stock","Unite","Producteur")
        self.tree = ttk.Treeview(frame_produits, columns=cols, show="headings", height=14)
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("Produit", width=150)
        self.tree.column("Categorie", width=80)
        self.tree.column("Prix (FCFA)", width=90)
        self.tree.column("Promo", width=55)
        self.tree.column("Prix final", width=90)
        self.tree.column("Stock", width=50)
        self.tree.column("Unite", width=50)
        self.tree.column("Producteur", width=140)
        self.tree.tag_configure("rupture", foreground="red")
        self.tree.tag_configure("promo", foreground="#27ae60")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        frame_add = tk.Frame(frame_produits, bg="#f5f0e8")
        frame_add.pack(pady=5)
        tk.Label(frame_add, text="Quantite:", bg="#f5f0e8").pack(side="left")
        self.qte_var = tk.IntVar(value=1)
        tk.Spinbox(frame_add, from_=1, to=50, textvariable=self.qte_var, width=5).pack(side="left", padx=5)
        tk.Label(frame_add, text="Livraison:", bg="#f5f0e8").pack(side="left", padx=(10,0))
        self.livraison_var = tk.StringVar(value="normal (500 FCFA)")
        ttk.Combobox(frame_add, textvariable=self.livraison_var,
                     values=["normal (500 FCFA)", "express (2000 FCFA)"],
                     width=18, state="readonly").pack(side="left", padx=4)
        tk.Button(frame_add, text="Ajouter au panier", command=self.ajouter_panier,
                  bg="#4a7c59", fg="white", padx=10).pack(side="left", padx=5)

        frame_panier = tk.LabelFrame(frame_main, text="Panier",
                                      bg="#f5f0e8", font=("Helvetica", 11, "bold"), width=330)
        frame_panier.pack(side="right", fill="y", padx=5)
        frame_panier.pack_propagate(False)

        tk.Label(frame_panier, text="Region livraison:", bg="#f5f0e8",
                 font=("Helvetica", 10)).pack(anchor="w", padx=5, pady=(5,0))
        self.region_var = tk.StringVar(value="Dakar")
        ttk.Combobox(frame_panier, textvariable=self.region_var,
                     values=REGIONS, width=20, state="readonly").pack(padx=5, fill="x")

        self.liste_panier = tk.Listbox(frame_panier, width=35, height=10, font=("Courier", 9))
        self.liste_panier.pack(padx=5, pady=5, fill="both", expand=True)

        tk.Button(frame_panier, text="Retirer", command=self.retirer_panier,
                  bg="#e74c3c", fg="white", width=20).pack(pady=2)

        self.label_total = tk.Label(frame_panier, text="Sous-total: 0 FCFA",
                                     font=("Helvetica", 11, "bold"), bg="#f5f0e8", fg="#4a7c59")
        self.label_total.pack(pady=2)
        self.label_promo = tk.Label(frame_panier, text="Reduction: 0 FCFA",
                                     font=("Helvetica", 10), bg="#f5f0e8", fg="#27ae60")
        self.label_promo.pack()
        self.label_frais = tk.Label(frame_panier, text="Livraison: 500 FCFA",
                                     font=("Helvetica", 10), bg="#f5f0e8", fg="#e67e22")
        self.label_frais.pack()
        self.label_total_final = tk.Label(frame_panier, text="TOTAL: 0 FCFA",
                                           font=("Helvetica", 13, "bold"), bg="#f5f0e8", fg="#2C5F2D")
        self.label_total_final.pack(pady=3)

        tk.Button(frame_panier, text="Commander", command=self.commander,
                  bg="#2980b9", fg="white", width=20, font=("Helvetica", 11, "bold")).pack(pady=5)
        tk.Button(frame_panier, text="Vider panier", command=self.vider_panier,
                  bg="#95a5a6", fg="white", width=20).pack(pady=2)

    def reinitialiser_filtres(self):
        self.categorie_var.set("Toutes")
        self.search_nom.set("")
        self.promo_var.set(0)
        self.charger_produits()

    def charger_produits(self):
        self.tree.delete(*self.tree.get_children())
        db = get_db()
        if not db:
            return
        filtre = {}
        if self.categorie_var.get() != "Toutes":
            filtre["categorie"] = self.categorie_var.get()
        nom = self.search_nom.get().strip()
        if nom:
            filtre["nom"] = {"$regex": nom, "$options": "i"}
        promo = self.promo_var.get()
        for p in db.produits.find(filtre).sort("categorie", 1):
            tag = "rupture" if p["stock"] < 5 else ""
            prix_final = int(p["prix"] * (1 - promo / 100))
            promo_str = str(promo) + "%" if promo > 0 else "-"
            if promo > 0 and p["stock"] >= 5:
                tag = "promo"
            self.tree.insert("", "end", iid=str(p["_id"]),
                             values=(p["nom"], p["categorie"],
                                     str(p["prix"]) + " FCFA",
                                     promo_str,
                                     str(prix_final) + " FCFA",
                                     p["stock"],
                                     p.get("unite", "kg"),
                                     p["producteur"]),
                             tags=(tag,))

    def ajouter_panier(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Selectionnez un produit !")
            return
        db = get_db()
        if not db:
            return
        from bson import ObjectId
        produit = db.produits.find_one({"_id": ObjectId(selection[0])})
        qte = self.qte_var.get()
        if produit["stock"] < qte:
            messagebox.showerror("Stock insuffisant", "Stock disponible: " + str(produit["stock"]))
            return
        promo = self.promo_var.get()
        prix_final = int(produit["prix"] * (1 - promo / 100))
        self.panier.append({
            "produit_id": produit["_id"],
            "nom": produit["nom"],
            "quantite": qte,
            "prix_unitaire": produit["prix"],
            "prix_final": prix_final,
            "promo": promo,
            "unite": produit.get("unite", "kg"),
        })
        self.maj_panier()

    def maj_panier(self):
        self.liste_panier.delete(0, "end")
        sous_total = 0
        reduction = 0
        for item in self.panier:
            sous_total_item = item["quantite"] * item["prix_unitaire"]
            final_item = item["quantite"] * item["prix_final"]
            reduction += sous_total_item - final_item
            sous_total += sous_total_item
            promo_str = " (-" + str(item["promo"]) + "%)" if item["promo"] > 0 else ""
            self.liste_panier.insert("end",
                item["nom"][:16] + " x" + str(item["quantite"]) + " = " + str(final_item) + " FCFA" + promo_str)
        livraison = self.livraison_var.get()
        frais = 2000 if "express" in livraison else 500
        total_final = sous_total - reduction + frais
        self.label_total.config(text="Sous-total: " + str(sous_total) + " FCFA")
        self.label_promo.config(text="Reduction: -" + str(reduction) + " FCFA")
        self.label_frais.config(text="Livraison: " + str(frais) + " FCFA")
        self.label_total_final.config(text="TOTAL: " + str(total_final) + " FCFA")

    def retirer_panier(self):
        sel = self.liste_panier.curselection()
        if sel:
            self.panier.pop(sel[0])
            self.maj_panier()

    def vider_panier(self):
        self.panier = []
        self.maj_panier()

    def commander(self):
        if not self.panier:
            messagebox.showwarning("Panier vide", "Ajoutez des produits !")
            return
        db = get_db()
        if not db:
            return
        client = random.choice(CLIENTS)
        sous_total = sum(i["quantite"] * i["prix_unitaire"] for i in self.panier)
        total_final = sum(i["quantite"] * i["prix_final"] for i in self.panier)
        reduction = sous_total - total_final
        livraison = self.livraison_var.get()
        frais = 2000 if "express" in livraison else 500
        region = self.region_var.get()
        type_liv = "express" if "express" in livraison else "normal"
        total_avec_frais = total_final + frais

        commande = {
            "client": client,
            "date": datetime.now(),
            "articles": self.panier.copy(),
            "statut": "en_attente",
            "sous_total": round(sous_total, 2),
            "reduction": round(reduction, 2),
            "total": round(total_avec_frais, 2),
            "devise": "FCFA",
            "livraison": {
                "type": type_liv,
                "frais": frais,
                "adresse": "Quartier " + region,
                "ville": region,
                "region": region
            }
        }
        for item in self.panier:
            db.produits.update_one({"_id": item["produit_id"]}, {"$inc": {"stock": -item["quantite"]}})
        db.commandes.insert_one(commande)
        log_info("Commande passee - " + client["nom"] + " - " + str(total_avec_frais) + " FCFA - " + region)
        messagebox.showinfo("Commande confirmee !",
            "Client: " + client["nom"] + "\n" +
            "Tel: " + client["telephone"] + "\n" +
            "Region: " + region + "\n" +
            "Livraison: " + type_liv + " (" + str(frais) + " FCFA)\n" +
            "Sous-total: " + str(sous_total) + " FCFA\n" +
            "Reduction: -" + str(reduction) + " FCFA\n" +
            "TOTAL: " + str(total_avec_frais) + " FCFA"
        )
        self.vider_panier()
        self.charger_produits()
        self.verifier_stock_bas()

    def toggle_generateur(self):
        self.generateur_actif = not self.generateur_actif
        if self.generateur_actif:
            self.btn_gen.config(text="Generateur ON", bg="#27ae60")
            threading.Thread(target=self.run_generateur, daemon=True).start()
            log_info("Generateur demarre")
        else:
            self.btn_gen.config(text="Generateur OFF", bg="#c0392b")
            log_info("Generateur arrete")

    def run_generateur(self):
        while self.generateur_actif:
            try:
                db = get_db()
                if not db:
                    break
                produits = list(db.produits.find({"stock": {"$gt": 0}}))
                if produits:
                    choisis = random.sample(produits, min(random.randint(1,3), len(produits)))
                    articles = []
                    for p in choisis:
                        qte = random.randint(1, min(5, p["stock"]))
                        articles.append({"produit_id": p["_id"], "nom_produit": p["nom"],
                                         "quantite": qte, "prix_unitaire": p["prix"], "prix_final": p["prix"], "promo": 0})
                        db.produits.update_one({"_id": p["_id"]}, {"$inc": {"stock": -qte}})
                    total = sum(a["quantite"] * a["prix_unitaire"] for a in articles)
                    client = random.choice(CLIENTS)
                    livraison = random.choice(["normal", "express"])
                    frais = 2000 if livraison == "express" else 500
                    db.commandes.insert_one({
                        "client": client, "date": datetime.now(), "articles": articles,
                        "statut": "confirmee", "total": round(total + frais, 2), "devise": "FCFA",
                        "livraison": {"type": livraison, "frais": frais,
                                      "ville": client["ville"], "region": client["ville"]}
                    })
                    self.root.after(0, self.charger_produits)
            except Exception as e:
                log_erreur("Erreur generateur : " + str(e))
            time.sleep(60)

    def build_stats(self):
        frame_top = tk.Frame(self.frame_stats, bg="#f5f0e8")
        frame_top.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_top, text="Tableau de bord", font=("Helvetica", 15, "bold"),
                 bg="#f5f0e8", fg="#4a7c59").pack(side="left")
        tk.Button(frame_top, text="Actualiser", command=self.charger_stats,
                  bg="#4a7c59", fg="white", padx=10).pack(side="right")

        self.notebook_stats = ttk.Notebook(self.frame_stats)
        self.notebook_stats.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_globales = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_globales, text="Globales")
        self.frame_ca = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_ca, text="CA Categorie")
        self.frame_regions = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_regions, text="CA Regions")
        self.frame_livraison = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_livraison, text="Livraisons")
        self.frame_clients = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_clients, text="Top Clients")
        self.frame_ruptures = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_ruptures, text="Ruptures")
        self.frame_historique = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_historique, text="Historique")
        self.frame_evolution = tk.Frame(self.notebook_stats, bg="#1e1e1e")
        self.notebook_stats.add(self.frame_evolution, text="Evolution")

        self.text_globales = self._make_text(self.frame_globales)
        self.text_ca = self._make_text(self.frame_ca)
        self.text_regions = self._make_text(self.frame_regions)
        self.text_livraison = self._make_text(self.frame_livraison)
        self.text_clients = self._make_text(self.frame_clients)
        self.text_ruptures = self._make_text(self.frame_ruptures)
        self.text_evolution = self._make_text(self.frame_evolution)

        frame_search = tk.Frame(self.frame_historique, bg="#1e1e1e")
        frame_search.pack(fill="x", padx=5, pady=5)
        tk.Label(frame_search, text="Email:", bg="#1e1e1e", fg="white").pack(side="left")
        self.email_var = tk.StringVar(value="amadou.diallo@gmail.com")
        ttk.Combobox(frame_search, textvariable=self.email_var,
                     values=[c["email"] for c in CLIENTS], width=30).pack(side="left", padx=5)
        tk.Button(frame_search, text="Rechercher", command=self.charger_historique_client,
                  bg="#2980b9", fg="white", padx=8).pack(side="left")
        self.text_historique = self._make_text(self.frame_historique)

    def _make_text(self, parent):
        frame = tk.Frame(parent, bg="#1e1e1e")
        frame.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        txt = tk.Text(frame, font=("Courier", 10), bg="#1e1e1e", fg="#00ff88",
                      yscrollcommand=scroll.set, wrap="none")
        txt.pack(fill="both", expand=True, padx=5, pady=5)
        scroll.config(command=txt.yview)
        return txt

    def on_tab_change(self, event):
        tab = self.notebook.index(self.notebook.select())
        if self.role == "administrateur" and tab == 1:
            self.charger_stats()

    def charger_stats(self):
        self.charger_globales()
        self.charger_ca_categorie()
        self.charger_regions()
        self.charger_livraisons()
        self.charger_top_clients()
        self.charger_ruptures()
        self.charger_evolution()
        self.charger_historique_client()

    def charger_globales(self):
        db = get_db()
        if not db:
            return
        nb_produits = db.produits.count_documents({})
        nb_commandes = db.commandes.count_documents({})
        nb_ruptures = db.produits.count_documents({"stock": {"$lt": 5}})
        agg = list(db.commandes.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total"}, "moyenne": {"$avg": "$total"}}}]))
        ca_total = agg[0]["total"] if agg else 0
        panier_moyen = agg[0]["moyenne"] if agg else 0
        pipeline = [{"$unwind": "$articles"}, {"$group": {"_id": "$articles.produit_id", "nom": {"$first": "$articles.nom_produit"}, "qte": {"$sum": "$articles.quantite"}}}, {"$sort": {"qte": -1}}, {"$limit": 5}]
        t = self.text_globales
        t.delete(1.0, "end")
        t.insert("end", "STATISTIQUES GLOBALES\n\n")
        t.insert("end", "Produits     : " + str(nb_produits) + "\n")
        t.insert("end", "Commandes    : " + str(nb_commandes) + "\n")
        t.insert("end", "Ruptures     : " + str(nb_ruptures) + "\n")
        t.insert("end", "CA total     : " + str(round(ca_total,2)) + " FCFA\n")
        t.insert("end", "Panier moyen : " + str(round(panier_moyen,2)) + " FCFA\n\n")
        t.insert("end", "TOP 5 PRODUITS\n" + "-"*45 + "\n")
        for i, r in enumerate(db.commandes.aggregate(pipeline), 1):
            t.insert("end", str(i) + ". " + r["nom"] + " - " + str(r["qte"]) + " unites\n")

    def charger_ca_categorie(self):
        db = get_db()
        if not db:
            return
        pipeline = [{"$unwind": "$articles"}, {"$lookup": {"from": "produits", "localField": "articles.produit_id", "foreignField": "_id", "as": "info"}}, {"$unwind": "$info"}, {"$group": {"_id": "$info.categorie", "ca": {"$sum": {"$multiply": ["$articles.quantite", "$articles.prix_unitaire"]}}, "qte": {"$sum": "$articles.quantite"}}}, {"$sort": {"ca": -1}}]
        resultats = list(db.commandes.aggregate(pipeline))
        total = sum(r["ca"] for r in resultats)
        t = self.text_ca
        t.delete(1.0, "end")
        t.insert("end", "CA PAR CATEGORIE\n\n")
        for r in resultats:
            pct = (r["ca"] / total * 100) if total > 0 else 0
            barre = "#" * int(pct / 2)
            t.insert("end", r["_id"] + " : " + str(round(r["ca"],2)) + " FCFA (" + str(round(pct,1)) + "%)\n")
            t.insert("end", "  [" + barre.ljust(50) + "]\n\n")
        t.insert("end", "TOTAL : " + str(round(total,2)) + " FCFA\n")

    def charger_regions(self):
        db = get_db()
        if not db:
            return
        pipeline = [{"$group": {"_id": "$livraison.region", "nb": {"$sum": 1}, "ca": {"$sum": "$total"}}}, {"$sort": {"ca": -1}}]
        resultats = list(db.commandes.aggregate(pipeline))
        total = sum(r["ca"] for r in resultats if r["_id"])
        t = self.text_regions
        t.delete(1.0, "end")
        t.insert("end", "CA PAR REGION\n\n")
        for r in resultats:
            if r["_id"]:
                pct = (r["ca"] / total * 100) if total > 0 else 0
                barre = "#" * int(pct / 2)
                t.insert("end", r["_id"] + " : " + str(round(r["ca"],2)) + " FCFA (" + str(r["nb"]) + " cmd)\n")
                t.insert("end", "  [" + barre.ljust(50) + "]\n\n")
        t.insert("end", "TOTAL : " + str(round(total,2)) + " FCFA\n")

    def charger_livraisons(self):
        db = get_db()
        if not db:
            return
        pipeline = [{"$group": {"_id": "$livraison.type", "nb": {"$sum": 1}, "ca_frais": {"$sum": "$livraison.frais"}}}, {"$sort": {"nb": -1}}]
        resultats = list(db.commandes.aggregate(pipeline))
        t = self.text_livraison
        t.delete(1.0, "end")
        t.insert("end", "STATS PAR LIVRAISON\n\n")
        total_cmd = sum(r["nb"] for r in resultats)
        for r in resultats:
            if r["_id"]:
                pct = (r["nb"] / total_cmd * 100) if total_cmd > 0 else 0
                t.insert("end", "Type: " + r["_id"].upper() + "\n")
                t.insert("end", "  Commandes  : " + str(r["nb"]) + " (" + str(round(pct,1)) + "%)\n")
                t.insert("end", "  Frais total: " + str(round(r["ca_frais"] or 0,2)) + " FCFA\n\n")
        t.insert("end", "TOTAL : " + str(total_cmd) + " commandes\n")

    def charger_top_clients(self):
        db = get_db()
        if not db:
            return
        pipeline = [
            {"$group": {"_id": "$client.email",
                        "nom": {"$first": "$client.nom"},
                        "tel": {"$first": "$client.telephone"},
                        "ville": {"$first": "$client.ville"},
                        "nb_commandes": {"$sum": 1},
                        "total_depense": {"$sum": "$total"}}},
            {"$sort": {"total_depense": -1}}, {"$limit": 14}
        ]
        resultats = list(db.commandes.aggregate(pipeline))
        t = self.text_clients
        t.delete(1.0, "end")
        t.insert("end", "TOP CLIENTS\n\n")
        for i, r in enumerate(resultats, 1):
            t.insert("end", str(i) + ". " + r["nom"] + "\n")
            t.insert("end", "   Tel     : " + str(r.get("tel","?")) + "\n")
            t.insert("end", "   Ville   : " + str(r.get("ville","?")) + "\n")
            t.insert("end", "   Cmds    : " + str(r["nb_commandes"]) + "\n")
            t.insert("end", "   Depense : " + str(round(r["total_depense"],2)) + " FCFA\n\n")

    def charger_ruptures(self):
        db = get_db()
        if not db:
            return
        ruptures = list(db.produits.find({"stock": {"$lt": 5}}).sort("stock", 1))
        ok = list(db.produits.find({"stock": {"$gte": 5, "$lt": 20}}).sort("stock", 1))
        t = self.text_ruptures
        t.delete(1.0, "end")
        t.insert("end", "RUPTURES (stock < 5)\n\n")
        if not ruptures:
            t.insert("end", "Aucune rupture !\n")
        for p in ruptures:
            t.insert("end", p["nom"] + " - Stock: " + str(p["stock"]) + " [" + p["categorie"] + "]\n")
        t.insert("end", "\nSTOCK FAIBLE (5-20)\n\n")
        if not ok:
            t.insert("end", "Aucun stock faible !\n")
        for p in ok:
            t.insert("end", p["nom"] + " - Stock: " + str(p["stock"]) + "\n")

    def charger_historique_client(self):
        email = self.email_var.get().strip()
        db = get_db()
        if not db:
            return
        commandes = list(db.commandes.find({"client.email": email}).sort("date", -1))
        t = self.text_historique
        t.delete(1.0, "end")
        t.insert("end", "HISTORIQUE - " + email + "\n\n")
        if not commandes:
            t.insert("end", "Aucune commande.\n")
            return
        total_depenses = sum(c["total"] for c in commandes)
        t.insert("end", "Commandes : " + str(len(commandes)) + "   Total : " + str(round(total_depenses,2)) + " FCFA\n\n")
        for i, cmd in enumerate(commandes, 1):
            t.insert("end", "Commande #" + str(i) + " | " + cmd["date"].strftime("%d/%m/%Y %H:%M") + " | " + cmd["statut"] + "\n")
            t.insert("end", "Livraison: " + cmd.get("livraison",{}).get("type","?") + " -> " + cmd.get("livraison",{}).get("region","?") + "\n")
            for a in cmd["articles"]:
                nom = a.get("nom_produit", a.get("nom","?"))
                t.insert("end", "  - " + nom + " x" + str(a["quantite"]) + " @ " + str(a["prix_unitaire"]) + " FCFA\n")
            t.insert("end", "  Total: " + str(cmd["total"]) + " FCFA\n\n")

    def charger_evolution(self):
        db = get_db()
        if not db:
            return
        pipeline = [{"$group": {"_id": {"jour": {"$dayOfMonth": "$date"}, "mois": {"$month": "$date"}, "annee": {"$year": "$date"}}, "nb": {"$sum": 1}, "ca": {"$sum": "$total"}}}, {"$sort": {"_id.annee": 1, "_id.mois": 1, "_id.jour": 1}}, {"$limit": 30}]
        resultats = list(db.commandes.aggregate(pipeline))
        t = self.text_evolution
        t.delete(1.0, "end")
        t.insert("end", "EVOLUTION DES VENTES\n\n")
        if not resultats:
            t.insert("end", "Aucune donnee.\n")
            return
        max_ca = max(r["ca"] for r in resultats)
        for r in resultats:
            date_str = str(r["_id"]["jour"]) + "/" + str(r["_id"]["mois"]) + "/" + str(r["_id"]["annee"])
            barre = "#" * int(r["ca"] / max_ca * 40)
            t.insert("end", date_str + "  " + barre + "  " + str(round(r["ca"],2)) + " FCFA (" + str(r["nb"]) + " cmd)\n")

    def build_admin(self):
        tk.Label(self.frame_admin, text="Administration - Terroir Local Senegal",
                 font=("Helvetica", 15, "bold"), bg="#f5f0e8", fg="#2C5F2D").pack(pady=10)

        notebook_admin = ttk.Notebook(self.frame_admin)
        notebook_admin.pack(fill="both", expand=True, padx=10, pady=5)

        frame_produit = tk.Frame(notebook_admin, bg="#f5f0e8")
        notebook_admin.add(frame_produit, text="Gestion Produits")
        frame_stock_prix = tk.Frame(notebook_admin, bg="#f5f0e8")
        notebook_admin.add(frame_stock_prix, text="Stock et Prix")
        frame_utilisateurs = tk.Frame(notebook_admin, bg="#f5f0e8")
        notebook_admin.add(frame_utilisateurs, text="Utilisateurs")
        frame_actions = tk.Frame(notebook_admin, bg="#f5f0e8")
        notebook_admin.add(frame_actions, text="Actions et Backup")

        # ── GESTION PRODUITS ──
        tk.Label(frame_produit, text="Ajouter un nouveau produit",
                 font=("Helvetica", 13, "bold"), bg="#f5f0e8", fg="#2C5F2D").pack(pady=10)
        frame_form = tk.Frame(frame_produit, bg="#f5f0e8")
        frame_form.pack(padx=20, fill="x")
        labels = ["Nom:", "Categorie:", "Prix (FCFA):", "Stock:", "Unite:", "Producteur:", "Origine:"]
        self.champs_produit = {}
        for i, label in enumerate(labels):
            tk.Label(frame_form, text=label, bg="#f5f0e8", width=15, anchor="w").grid(row=i, column=0, pady=4, sticky="w")
            if label == "Categorie:":
                entry = ttk.Combobox(frame_form, values=CATEGORIES, width=25, state="readonly")
            elif label == "Unite:":
                entry = ttk.Combobox(frame_form, values=["kg","litre","unite","botte","sac"], width=25, state="readonly")
            else:
                entry = tk.Entry(frame_form, width=27)
            entry.grid(row=i, column=1, pady=4, padx=5)
            self.champs_produit[label] = entry

        tk.Button(frame_produit, text="Ajouter le produit", command=self.ajouter_produit,
                  bg="#2C5F2D", fg="white", font=("Helvetica", 11, "bold"), padx=15, pady=6).pack(pady=5)

        frame_sup = tk.Frame(frame_produit, bg="#f5f0e8")
        frame_sup.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_sup, text="Supprimer produit:", bg="#f5f0e8", font=("Helvetica", 11, "bold")).pack(side="left")
        self.entry_supprimer = tk.Entry(frame_sup, width=25)
        self.entry_supprimer.pack(side="left", padx=5)
        tk.Button(frame_sup, text="Supprimer", command=self.supprimer_produit,
                  bg="#c0392b", fg="white", padx=10).pack(side="left")

        # ── STOCK ET PRIX ──
        tk.Label(frame_stock_prix, text="Modifier le stock",
                 font=("Helvetica", 12, "bold"), bg="#f5f0e8", fg="#2C5F2D").pack(pady=10)
        frame_s = tk.Frame(frame_stock_prix, bg="#f5f0e8")
        frame_s.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_s, text="Produit:", bg="#f5f0e8").pack(side="left")
        self.admin_produit = tk.Entry(frame_s, width=25)
        self.admin_produit.pack(side="left", padx=5)
        tk.Label(frame_s, text="Stock:", bg="#f5f0e8").pack(side="left")
        self.admin_stock = tk.Entry(frame_s, width=8)
        self.admin_stock.pack(side="left", padx=5)
        tk.Button(frame_s, text="Mettre a jour", command=self.maj_stock_admin,
                  bg="#4a7c59", fg="white", padx=8).pack(side="left", padx=5)

        tk.Label(frame_stock_prix, text="Modifier le prix",
                 font=("Helvetica", 12, "bold"), bg="#f5f0e8", fg="#2C5F2D").pack(pady=10)
        frame_p = tk.Frame(frame_stock_prix, bg="#f5f0e8")
        frame_p.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_p, text="Produit:", bg="#f5f0e8").pack(side="left")
        self.admin_produit_prix = tk.Entry(frame_p, width=25)
        self.admin_produit_prix.pack(side="left", padx=5)
        tk.Label(frame_p, text="Prix FCFA:", bg="#f5f0e8").pack(side="left")
        self.admin_prix = tk.Entry(frame_p, width=10)
        self.admin_prix.pack(side="left", padx=5)
        tk.Button(frame_p, text="Mettre a jour", command=self.maj_prix_admin,
                  bg="#2980b9", fg="white", padx=8).pack(side="left", padx=5)

        # ── UTILISATEURS ──
        tk.Label(frame_utilisateurs, text="Gestion des Utilisateurs",
                 font=("Helvetica", 13, "bold"), bg="#f5f0e8", fg="#2C5F2D").pack(pady=10)

        frame_u = tk.Frame(frame_utilisateurs, bg="#f5f0e8")
        frame_u.pack(fill="x", padx=20, pady=5)

        champs_u = ["Login:", "Mot de passe:", "Nom complet:", "Email:", "Role:"]
        self.champs_user = {}
        for i, label in enumerate(champs_u):
            tk.Label(frame_u, text=label, bg="#f5f0e8", width=15, anchor="w").grid(row=i, column=0, pady=3)
            if label == "Role:":
                entry = ttk.Combobox(frame_u, values=["utilisateur","administrateur"], width=22, state="readonly")
            else:
                entry = tk.Entry(frame_u, width=24, show="*" if label == "Mot de passe:" else "")
            entry.grid(row=i, column=1, pady=3, padx=5)
            self.champs_user[label] = entry

        frame_u_btn = tk.Frame(frame_utilisateurs, bg="#f5f0e8")
        frame_u_btn.pack(pady=5)
        tk.Button(frame_u_btn, text="Ajouter utilisateur", command=self.ajouter_user,
                  bg="#2C5F2D", fg="white", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(frame_u_btn, text="Supprimer utilisateur (login)", command=self.supprimer_user,
                  bg="#c0392b", fg="white", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(frame_u_btn, text="Lister utilisateurs", command=self.lister_users,
                  bg="#2980b9", fg="white", padx=10, pady=5).pack(side="left", padx=5)

        self.text_users = tk.Text(frame_utilisateurs, font=("Courier", 10), bg="#1e1e1e", fg="#00ff88", height=8)
        self.text_users.pack(fill="both", expand=True, padx=20, pady=5)

        # ── ACTIONS ET BACKUP ──
        frame_a = tk.Frame(frame_actions, bg="#f5f0e8")
        frame_a.pack(fill="x", padx=20, pady=15)
        tk.Button(frame_a, text="Reinitialiser stocks", command=self.reinitialiser_db,
                  bg="#e67e22", fg="white", padx=10, pady=8, font=("Helvetica", 11)).pack(side="left", padx=5)
        tk.Button(frame_a, text="Supprimer commandes", command=self.supprimer_commandes,
                  bg="#c0392b", fg="white", padx=10, pady=8, font=("Helvetica", 11)).pack(side="left", padx=5)
        tk.Button(frame_a, text="Backup maintenant", command=self.faire_backup_maintenant,
                  bg="#8e44ad", fg="white", padx=10, pady=8, font=("Helvetica", 11)).pack(side="left", padx=5)
        tk.Button(frame_a, text="Verifier stocks bas", command=self.verifier_stock_bas,
                  bg="#d35400", fg="white", padx=10, pady=8, font=("Helvetica", 11)).pack(side="left", padx=5)

        tk.Label(frame_actions, text="Backups disponibles :",
                 font=("Helvetica", 11, "bold"), bg="#f5f0e8").pack(anchor="w", padx=20)
        self.text_backups = tk.Text(frame_actions, font=("Courier", 9), bg="#1e1e1e", fg="#00ff88", height=5)
        self.text_backups.pack(fill="x", padx=20, pady=5)
        self.afficher_backups()

        frame_log = tk.LabelFrame(frame_actions, text="Journal d'actions",
                                   bg="#f5f0e8", font=("Helvetica", 11, "bold"))
        frame_log.pack(fill="both", expand=True, padx=20, pady=5)
        self.text_log = tk.Text(frame_log, font=("Courier", 10), bg="#1e1e1e", fg="#00ff88", height=8)
        self.text_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.log("Panneau admin pret.")

    def afficher_backups(self):
        self.text_backups.delete(1.0, "end")
        fichiers = lister_backups()
        if not fichiers:
            self.text_backups.insert("end", "Aucun backup disponible.\n")
        for f in fichiers:
            taille = os.path.getsize(BACKUP_DIR + f)
            self.text_backups.insert("end", f + " (" + str(taille) + " octets)\n")

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.text_log.insert("end", "[" + now + "] " + message + "\n")
        self.text_log.see("end")
        log_info(message)

    def ajouter_produit(self):
        nom = self.champs_produit["Nom:"].get().strip()
        categorie = self.champs_produit["Categorie:"].get().strip()
        prix_str = self.champs_produit["Prix (FCFA):"].get().strip()
        stock_str = self.champs_produit["Stock:"].get().strip()
        unite = self.champs_produit["Unite:"].get().strip()
        producteur = self.champs_produit["Producteur:"].get().strip()
        origine = self.champs_produit["Origine:"].get().strip()
        if not all([nom, categorie, prix_str, stock_str, unite, producteur]):
            messagebox.showwarning("Erreur", "Remplissez tous les champs !")
            return
        try:
            prix = int(prix_str)
            stock = int(stock_str)
        except:
            messagebox.showerror("Erreur", "Prix et stock doivent etre des nombres !")
            return
        db = get_db()
        if not db:
            return
        if db.produits.find_one({"nom": nom}):
            messagebox.showerror("Erreur", "Ce produit existe deja !")
            return
        db.produits.insert_one({
            "nom": nom, "categorie": categorie, "prix": prix,
            "stock": stock, "unite": unite, "producteur": producteur,
            "image": "📦", "attributs": {"origine": origine, "bio": False}
        })
        self.log("Produit ajoute : " + nom + " - " + str(prix) + " FCFA")
        messagebox.showinfo("OK", "Produit " + nom + " ajoute !")
        self.charger_produits()

    def supprimer_produit(self):
        nom = self.entry_supprimer.get().strip()
        if not nom:
            messagebox.showwarning("Erreur", "Entrez le nom du produit !")
            return
        if messagebox.askyesno("Confirmation", "Supprimer : " + nom + " ?"):
            db = get_db()
            if not db:
                return
            result = db.produits.delete_one({"nom": {"$regex": nom, "$options": "i"}})
            if result.deleted_count > 0:
                self.log("Produit supprime : " + nom)
                messagebox.showinfo("OK", "Produit supprime !")
                self.charger_produits()
            else:
                messagebox.showerror("Erreur", "Produit introuvable !")

    def maj_stock_admin(self):
        nom = self.admin_produit.get().strip()
        stock_str = self.admin_stock.get().strip()
        if not nom or not stock_str:
            messagebox.showwarning("Erreur", "Remplissez les deux champs !")
            return
        try:
            stock = int(stock_str)
        except:
            messagebox.showerror("Erreur", "Stock doit etre un nombre !")
            return
        db = get_db()
        if not db:
            return
        result = db.produits.update_one(
            {"nom": {"$regex": nom, "$options": "i"}},
            {"$set": {"stock": stock}}
        )
        if result.modified_count > 0:
            self.log("Stock mis a jour : " + nom + " -> " + str(stock))
            messagebox.showinfo("OK", "Stock mis a jour !")
            self.charger_produits()
        else:
            messagebox.showerror("Erreur", "Produit introuvable !")

    def maj_prix_admin(self):
        nom = self.admin_produit_prix.get().strip()
        prix_str = self.admin_prix.get().strip()
        if not nom or not prix_str:
            messagebox.showwarning("Erreur", "Remplissez les deux champs !")
            return
        try:
            prix = int(prix_str)
        except:
            messagebox.showerror("Erreur", "Prix doit etre un nombre !")
            return
        db = get_db()
        if not db:
            return
        result = db.produits.update_one(
            {"nom": {"$regex": nom, "$options": "i"}},
            {"$set": {"prix": prix}}
        )
        if result.modified_count > 0:
            self.log("Prix mis a jour : " + nom + " -> " + str(prix) + " FCFA")
            messagebox.showinfo("OK", "Prix mis a jour !")
            self.charger_produits()
        else:
            messagebox.showerror("Erreur", "Produit introuvable !")

    def ajouter_user(self):
        login = self.champs_user["Login:"].get().strip()
        password = self.champs_user["Mot de passe:"].get().strip()
        nom = self.champs_user["Nom complet:"].get().strip()
        email = self.champs_user["Email:"].get().strip()
        role = self.champs_user["Role:"].get().strip()
        if not all([login, password, nom, email, role]):
            messagebox.showwarning("Erreur", "Remplissez tous les champs !")
            return
        ok, msg = ajouter_utilisateur(login, password, role, nom, email)
        if ok:
            self.log("Utilisateur ajoute : " + login + " (" + role + ")")
            messagebox.showinfo("OK", msg)
            self.lister_users()
        else:
            messagebox.showerror("Erreur", msg)

    def supprimer_user(self):
        login = self.champs_user["Login:"].get().strip()
        if not login:
            messagebox.showwarning("Erreur", "Entrez le login a supprimer !")
            return
        if messagebox.askyesno("Confirmation", "Supprimer l'utilisateur : " + login + " ?"):
            ok, msg = supprimer_utilisateur(login)
            if ok:
                self.log("Utilisateur supprime : " + login)
                messagebox.showinfo("OK", msg)
                self.lister_users()
            else:
                messagebox.showerror("Erreur", msg)

    def lister_users(self):
        self.text_users.delete(1.0, "end")
        users = lister_utilisateurs()
        self.text_users.insert("end", "UTILISATEURS ENREGISTRES\n\n")
        for u in users:
            self.text_users.insert("end", "Login: " + u[0] + "  Role: " + u[1] + "  Nom: " + u[2] + "\n")

    def reinitialiser_db(self):
        if messagebox.askyesno("Confirmation", "Reinitialiser tous les stocks ?"):
            import importlib
            sys.path.insert(0, "/home/ibrahima/terroir_local")
            import setup_db as sdb
            importlib.reload(sdb)
            sdb.creer_produits()
            self.log("Stocks reinitialises !")
            messagebox.showinfo("OK", "Stocks reinitialises !")
            self.charger_produits()

    def supprimer_commandes(self):
        if messagebox.askyesno("Confirmation", "Supprimer toutes les commandes ?"):
            db = get_db()
            if not db:
                return
            result = db.commandes.delete_many({})
            self.log(str(result.deleted_count) + " commandes supprimees !")
            messagebox.showinfo("OK", str(result.deleted_count) + " commandes supprimees !")

    def faire_backup_maintenant(self):
        fichier = faire_backup()
        if fichier:
            self.log("Backup cree : " + fichier)
            messagebox.showinfo("Backup OK", "Backup sauvegarde !")
            self.afficher_backups()
        else:
            messagebox.showerror("Erreur", "Backup echoue !")


def main():
    login_root = tk.Tk()
    login_win = LoginWindow(login_root)
    login_root.mainloop()
    if login_win.role:
        app_root = tk.Tk()
        TerroirApp(app_root, login_win.role)
        app_root.mainloop()

if __name__ == "__main__":
    main()
