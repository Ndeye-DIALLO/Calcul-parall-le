import csv
from datetime import datetime

fichier = "resultats.csv"
temporaire = "resultats_corrige.csv"

with open(fichier, "r", newline="") as f:
    lecteur = csv.DictReader(f)
    colonnes = lecteur.fieldnames
    lignes = list(lecteur)

for ligne in lignes:
    if ligne["taille"] == "1500":
        heure = datetime.fromisoformat(ligne["date"])

        if heure.hour >= 19:
            ligne["essai"] = str(int(ligne["essai"]) + 5)

with open(temporaire, "w", newline="") as f:
    ecrivain = csv.DictWriter(f, fieldnames=colonnes)
    ecrivain.writeheader()
    ecrivain.writerows(lignes)

print("Correction terminée : resultats_corrige.csv")

