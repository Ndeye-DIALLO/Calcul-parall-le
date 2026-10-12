import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

RACINE = Path(__file__).resolve().parent
FICHIER_ENTREE = RACINE / "resultats.csv"
FICHIER_SORTIE = RACINE / "statistiques.csv"

COLONNES_SORTIE = [
    "version",
    "mpi",
    "omp",
    "taille",
    "repetitions",
    "calcul_moyen",
    "calcul_ecart_type",
    "total_moyen",
    "total_ecart_type",
    "acceleration",
    "efficacite_pct",
]


# ============================================================
# FONCTIONS STATISTIQUES
# ============================================================

def moyenne(valeurs):
    """Calcule la moyenne d'une liste de valeurs."""
    return sum(valeurs) / len(valeurs) if valeurs else None


def ecart_type(valeurs):
    """Calcule l'écart-type de population."""
    if not valeurs:
        return None

    m = moyenne(valeurs)
    variance = sum((x - m) ** 2 for x in valeurs) / len(valeurs)

    return math.sqrt(variance)


def formater(valeur):
    """Formate une valeur numérique pour l'affichage CSV."""
    if valeur is None:
        return ""
    return f"{valeur:.6f}"

def lire_resultats():
    if not FICHIER_ENTREE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {FICHIER_ENTREE}"
        )

    groupes = defaultdict(
        lambda: {
            "calcul": [],
            "total": [],
        }
    )

    with open(
        FICHIER_ENTREE,
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:
        lecteur = csv.DictReader(fichier)

        colonnes_requises = {
            "version",
            "processus_mpi",
            "threads_omp",
            "taille",
            "calcul_s",
            "total_s",
        }

        colonnes_presentes = set(lecteur.fieldnames or [])
        manquantes = colonnes_requises - colonnes_presentes

        if manquantes:
            raise ValueError(
                "Colonnes manquantes dans resultats.csv : "
                + ", ".join(sorted(manquantes))
            )

        for numero_ligne, ligne in enumerate(lecteur, start=2):
            try:
                version = ligne["version"].strip()
                mpi = int(ligne["processus_mpi"])
                omp = int(ligne["threads_omp"])
                taille = int(ligne["taille"])
                temps_calcul = float(ligne["calcul_s"])
                temps_total = float(ligne["total_s"])

                if not version:
                    raise ValueError("version vide")

                if mpi < 1 or omp < 1 or taille < 1:
                    raise ValueError("paramètre non positif")

                if (
                    not math.isfinite(temps_calcul)
                    or not math.isfinite(temps_total)
                    or temps_calcul < 0
                    or temps_total < 0
                ):
                    raise ValueError("temps invalide")

            except (ValueError, TypeError, KeyError) as erreur:
                raise ValueError(
                    f"Erreur à la ligne {numero_ligne} : {erreur}"
                ) from erreur

            cle = (version, mpi, omp, taille)

            groupes[cle]["calcul"].append(temps_calcul)
            groupes[cle]["total"].append(temps_total)

    if not groupes:
        raise ValueError(
            "Aucun résultat exploitable dans resultats.csv."
        )

    return groupes


# ============================================================
# LECTURE DES RÉSULTATS
# ============================================================

            

# ============================================================
# CALCUL DES STATISTIQUES
# ============================================================

def calculer_statistiques(groupes):
    statistiques = []

    for (version, mpi, omp, taille), donnees in groupes.items():
        temps_calcul = donnees["calcul"]
        temps_total = donnees["total"]

        statistiques.append({
            "version": version,
            "mpi": mpi,
            "omp": omp,
            "taille": taille,
            "repetitions": len(temps_calcul),
            "calcul_moyen": moyenne(temps_calcul),
            "calcul_ecart_type": ecart_type(temps_calcul),
            "total_moyen": moyenne(temps_total),
            "total_ecart_type": ecart_type(temps_total),
            "acceleration": None,
            "efficacite_pct": None,
        })

    # Référence séquentielle pour chaque taille de matrice.
    references = {}

    for s in statistiques:
        if (
            s["version"].lower() == "seq"
            and s["mpi"] == 1
            and s["omp"] == 1
        ):
            references[s["taille"]] = s["calcul_moyen"]

    # Accélération et efficacité conventionnelle.
    for s in statistiques:
        temps_seq = references.get(s["taille"])

        if temps_seq is None:
            continue

        if s["calcul_moyen"] <= 0:
            continue

        acceleration = temps_seq / s["calcul_moyen"]
        s["acceleration"] = acceleration

        # La configuration séquentielle est la référence.
        if s["version"].lower() == "seq":
            s["efficacite_pct"] = 100.0
        else:
            nombre_travailleurs = s["mpi"] * s["omp"]

            s["efficacite_pct"] = (
                100.0 * acceleration / nombre_travailleurs
            )

    statistiques.sort(
        key=lambda s: (
            s["taille"],
            s["version"],
            s["mpi"],
            s["omp"],
        )
    )

    return statistiques


# ============================================================
# ÉCRITURE DU FICHIER STATISTIQUES
# ============================================================

def enregistrer_statistiques(statistiques):
    with open(
        FICHIER_SORTIE,
        "w",
        newline="",
        encoding="utf-8",
    ) as fichier:
        ecrivain = csv.DictWriter(
            fichier,
            fieldnames=COLONNES_SORTIE,
        )

        ecrivain.writeheader()

        for s in statistiques:
            ligne = {}

            for colonne in COLONNES_SORTIE:
                valeur = s[colonne]

                if colonne in {
                    "calcul_moyen",
                    "calcul_ecart_type",
                    "total_moyen",
                    "total_ecart_type",
                    "acceleration",
                    "efficacite_pct",
                }:
                    ligne[colonne] = formater(valeur)
                else:
                    ligne[colonne] = valeur

            ecrivain.writerow(ligne)


# ============================================================
# AFFICHAGE D'UN RÉSUMÉ
# ============================================================

def afficher_statistiques(statistiques):
    print("\n========== RÉSULTATS STATISTIQUES ==========\n")

    entete = (
        f"{'Version':<10}"
        f"{'MPI':>5}"
        f"{'OMP':>5}"
        f"{'N':>7}"
        f"{'Essais':>8}"
        f"{'Calcul moyen (s)':>19}"
        f"{'Écart-type (s)':>17}"
        f"{'Accélération':>15}"
        f"{'Efficacité (%)':>17}"
    )

    print(entete)
    print("-" * len(entete))

    for s in statistiques:
        acceleration = (
            f"{s['acceleration']:.3f}x"
            if s["acceleration"] is not None
            else "N/A"
        )

        efficacite = (
            f"{s['efficacite_pct']:.2f}"
            if s["efficacite_pct"] is not None
            else "N/A"
        )

        print(
            f"{s['version']:<10}"
            f"{s['mpi']:>5}"
            f"{s['omp']:>5}"
            f"{s['taille']:>7}"
            f"{s['repetitions']:>8}"
            f"{s['calcul_moyen']:>19.4f}"
            f"{s['calcul_ecart_type']:>17.4f}"
            f"{acceleration:>15}"
            f"{efficacite:>17}"
        )


# ============================================================
# GRAPHIQUES
# ============================================================

def generer_graphiques(statistiques):
    tailles = sorted({s["taille"] for s in statistiques})

    for taille in tailles:
        donnees = [
            s for s in statistiques
            if s["taille"] == taille
        ]

        etiquettes = [
            f"{s['version']}\nMPI={s['mpi']}, OMP={s['omp']}"
            for s in donnees
        ]

        # ----------------------------------------------------
        # 1. Temps moyen de calcul
        # ----------------------------------------------------

        valeurs_calcul = [
            s["calcul_moyen"] for s in donnees
        ]

        erreurs_calcul = [
            s["calcul_ecart_type"] for s in donnees
        ]

        plt.figure(figsize=(11, 6))
        plt.bar(
            range(len(donnees)),
            valeurs_calcul,
            yerr=erreurs_calcul,
            capsize=4,
        )
        plt.xticks(
            range(len(donnees)),
            etiquettes,
            rotation=25,
            ha="right",
        )
        plt.ylabel("Temps moyen de calcul (secondes)")
        plt.title(f"Temps de calcul selon la configuration — N={taille}")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(
            RACINE / f"temps_calcul_N{taille}.png",
            dpi=200,
        )
        plt.close()

        # ----------------------------------------------------
        # 2. Temps total moyen
        # ----------------------------------------------------

        valeurs_total = [
            s["total_moyen"] for s in donnees
        ]

        erreurs_total = [
            s["total_ecart_type"] for s in donnees
        ]

        plt.figure(figsize=(11, 6))
        plt.bar(
            range(len(donnees)),
            valeurs_total,
            yerr=erreurs_total,
            capsize=4,
        )
        plt.xticks(
            range(len(donnees)),
            etiquettes,
            rotation=25,
            ha="right",
        )
        plt.ylabel("Temps total moyen (secondes)")
        plt.title(f"Temps total selon la configuration — N={taille}")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(
            RACINE / f"temps_total_N{taille}.png",
            dpi=200,
        )
        plt.close()

        # ----------------------------------------------------
        # 3. Accélération
        # ----------------------------------------------------

        donnees_acc = [
            s for s in donnees
            if s["acceleration"] is not None
        ]

        if donnees_acc:
            etiquettes_acc = [
                f"{s['version']}\nMPI={s['mpi']}, OMP={s['omp']}"
                for s in donnees_acc
            ]

            valeurs_acc = [
                s["acceleration"] for s in donnees_acc
            ]

            plt.figure(figsize=(11, 6))
            plt.bar(
                range(len(donnees_acc)),
                valeurs_acc,
            )
            plt.xticks(
                range(len(donnees_acc)),
                etiquettes_acc,
                rotation=25,
                ha="right",
            )
            plt.ylabel("Accélération")
            plt.title(f"Accélération parallèle — N={taille}")
            plt.axhline(
                1,
                linestyle="--",
                label="Référence séquentielle (1x)",
            )
            plt.legend()
            plt.grid(axis="y", alpha=0.3)
            plt.tight_layout()
            plt.savefig(
                RACINE / f"acceleration_N{taille}.png",
                dpi=200,
            )
            plt.close()

        # ----------------------------------------------------
        # 4. Efficacité parallèle conventionnelle
        # ----------------------------------------------------

        donnees_eff = [
            s for s in donnees
            if s["version"].lower() != "seq"
            and s["efficacite_pct"] is not None
        ]

        if donnees_eff:
            etiquettes_eff = [
                f"{s['version']}\nMPI={s['mpi']}, OMP={s['omp']}"
                for s in donnees_eff
            ]

            valeurs_eff = [
                s["efficacite_pct"] for s in donnees_eff
            ]

            plt.figure(figsize=(11, 6))
            plt.bar(
                range(len(donnees_eff)),
                valeurs_eff,
            )
            plt.xticks(
                range(len(donnees_eff)),
                etiquettes_eff,
                rotation=25,
                ha="right",
            )
            plt.ylabel("Efficacité conventionnelle (%)")
            plt.title(f"Efficacité parallèle — N={taille}")
            plt.axhline(
                100,
                linestyle="--",
                label="Référence théorique (100 %)",
            )
            plt.legend()
            plt.grid(axis="y", alpha=0.3)
            plt.tight_layout()
            plt.savefig(
                RACINE / f"efficacite_N{taille}.png",
                dpi=200,
            )
            plt.close()


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    print(f"Lecture des données : {FICHIER_ENTREE}")

    groupes = lire_resultats()
    statistiques = calculer_statistiques(groupes)

    enregistrer_statistiques(statistiques)
    afficher_statistiques(statistiques)
    generer_graphiques(statistiques)

    print("\nAnalyse terminée.")
    print(f"Fichier statistique : {FICHIER_SORTIE}")
    print("Graphiques enregistrés dans :", RACINE)


if __name__ == "__main__":
    main()

