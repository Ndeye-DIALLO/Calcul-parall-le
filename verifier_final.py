import csv
import math
from collections import defaultdict
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
CSV_RESULTATS = DOSSIER / "resultats.csv"
CSV_STATS = DOSSIER / "statistiques.csv"

CONFIGURATIONS = {
    ("seq", 1, 1),
    ("omp", 1, 4),
    ("mpi", 4, 1),
    ("hybride", 1, 4),
    ("hybride", 4, 1),
}

GRAPHIQUES = [
    "temps_calcul_N{n}.png",
    "temps_total_N{n}.png",
    "acceleration_N{n}.png",
    "efficacite_N{n}.png",
]


def lire_csv(chemin):
    with open(chemin, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def proche(a, b, tol=1e-5):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def main():
    erreurs = []
    avertissements = []
    controles = []

    def ok(message):
        controles.append("OK : " + message)

    def erreur(message):
        erreurs.append("ERREUR : " + message)

    def avertissement(message):
        avertissements.append("À VÉRIFIER : " + message)

    # 1. Présence des fichiers
    if not CSV_RESULTATS.exists():
        print("ERREUR : resultats.csv introuvable.")
        return

    if not CSV_STATS.exists():
        print("ERREUR : statistiques.csv introuvable.")
        return

    resultats = lire_csv(CSV_RESULTATS)
    stats = lire_csv(CSV_STATS)

    if not resultats:
        print("ERREUR : resultats.csv est vide.")
        return

    champs = {
        "version", "processus_mpi", "threads_omp",
        "essai", "taille", "calcul_s", "total_s", "checksum"
    }

    colonnes = set(resultats[0])
    manquantes = champs - colonnes

    if manquantes:
        erreur("Colonnes absentes de resultats.csv : "
               + ", ".join(sorted(manquantes)))
        afficher(erreurs, avertissements, controles)
        return

    ok(f"{len(resultats)} mesures lues dans resultats.csv.")

    # 2. Contrôle des valeurs numériques
    groupes = defaultdict(list)
    cles_essais = set()
    lignes_valides = True

    for i, r in enumerate(resultats, start=2):
        try:
            version = r["version"].strip().lower()
            mpi = int(r["processus_mpi"])
            omp = int(r["threads_omp"])
            essai = int(r["essai"])
            n = int(r["taille"])
            calcul = float(r["calcul_s"])
            total = float(r["total_s"])
            checksum = float(r["checksum"])

            valeurs = [calcul, total, checksum]

            if (
                not version or mpi < 1 or omp < 1
                or essai < 1 or n < 1
                or not all(math.isfinite(x) for x in valeurs)
                or calcul < 0 or total < 0
            ):
                raise ValueError("valeur invalide ou non finie")

            if total + 1e-9 < calcul:
                avertissement(
                    f"Ligne {i} : temps total inférieur au temps de calcul."
                )

            cle_essai = (version, mpi, omp, n, essai)
            if cle_essai in cles_essais:
                avertissement(
                    f"Doublon de configuration/essai à la ligne {i} : "
                    f"{cle_essai}"
                )
            cles_essais.add(cle_essai)

            groupes[(version, mpi, omp, n)].append(r)

        except (ValueError, TypeError, KeyError) as e:
            erreur(f"Ligne {i} de resultats.csv : {e}")
            lignes_valides = False

    if lignes_valides:
        ok("Les champs numériques sont valides.")

    tailles = sorted({int(r["taille"]) for r in resultats})
    ok(f"Tailles de matrices trouvées : {tailles}.")

    # 3. Configurations et répétitions
    for n in tailles:
        presentes = {
            (v, mpi, omp)
            for (v, mpi, omp, taille) in groupes
            if taille == n
        }

        absentes = CONFIGURATIONS - presentes
        inattendues = presentes - CONFIGURATIONS

        if absentes:
            erreur(f"N={n} : configurations absentes : {sorted(absentes)}")
        if inattendues:
            avertissement(
                f"N={n} : configurations supplémentaires : "
                f"{sorted(inattendues)}"
            )
        if not absentes:
            ok(f"N={n} : les cinq configurations attendues sont présentes.")

        comptes = {
            (v, mpi, omp): len(lignes)
            for (v, mpi, omp, taille), lignes in groupes.items()
            if taille == n
        }

        if comptes and len(set(comptes.values())) == 1:
            ok(f"N={n} : toutes les configurations ont "
               f"{next(iter(comptes.values()))} répétitions.")
        elif comptes:
            avertissement(
                f"N={n} : nombres de répétitions différents : {comptes}"
            )

    # 4. Sommes de contrôle entre configurations
    checks_par_taille = defaultdict(list)
    for (version, mpi, omp, n), lignes in groupes.items():
        for r in lignes:
            checks_par_taille[n].append(
                (r["version"], r["processus_mpi"],
                 r["threads_omp"], float(r["checksum"]))
            )

    for n, valeurs in sorted(checks_par_taille.items()):
        sommes = [x[3] for x in valeurs]
        reference = sommes[0]
        maximum = max(abs(x - reference) for x in sommes)

        if all(proche(x, reference, tol=1e-8) for x in sommes):
            ok(f"N={n} : sommes de contrôle cohérentes "
               f"(écart maximal {maximum:.3e}).")
        else:
            erreur(
                f"N={n} : sommes de contrôle différentes ; "
                f"écart maximal {maximum:.6g}."
            )

    # 5. Vérification du fichier de statistiques
    champs_stats = {
        "version", "mpi", "omp", "taille", "repetitions",
        "calcul_moyen", "calcul_ecart_type", "total_moyen",
        "total_ecart_type", "acceleration", "efficacite_pct"
    }

    if stats and champs_stats.issubset(stats[0]):
        ok("Les colonnes attendues sont présentes dans statistiques.csv.")
    else:
        erreur("Colonnes manquantes ou statistiques.csv vide.")

    stats_index = {}
    for s in stats:
        try:
            cle = (
                s["version"].strip().lower(),
                int(s["mpi"]), int(s["omp"]), int(s["taille"])
            )
            if cle in stats_index:
                erreur(f"Configuration statistique dupliquée : {cle}")
            stats_index[cle] = s
        except (ValueError, KeyError) as e:
            erreur(f"Ligne invalide dans statistiques.csv : {e}")

    # Vérifie les moyennes, écarts-types et nombres d'essais recalculés.
    for cle, lignes in groupes.items():
        if cle not in stats_index:
            erreur(f"Statistique absente pour {cle}.")
            continue

        s = stats_index[cle]
        calculs = [float(r["calcul_s"]) for r in lignes]
        totaux = [float(r["total_s"]) for r in lignes]

        def moyenne(xs):
            return sum(xs) / len(xs)

        def ecart_type_population(xs):
            m = moyenne(xs)
            return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))

        attendus = {
            "repetitions": len(lignes),
            "calcul_moyen": moyenne(calculs),
            "calcul_ecart_type": ecart_type_population(calculs),
            "total_moyen": moyenne(totaux),
            "total_ecart_type": ecart_type_population(totaux),
        }

        for champ, attendu in attendus.items():
            try:
                obtenu = int(s[champ]) if champ == "repetitions" else float(s[champ])
                if not proche(obtenu, attendu):
                    erreur(
                        f"{cle} : {champ} = {obtenu}, "
                        f"valeur recalculée = {attendu}."
                    )
            except (ValueError, KeyError):
                erreur(f"{cle} : champ {champ} invalide.")

    if not erreurs:
        ok("Les statistiques correspondent aux mesures brutes.")

    # 6. Graphiques
    for n in tailles:
        absents = [
            nom.format(n=n)
            for nom in GRAPHIQUES
            if not (DOSSIER / nom.format(n=n)).exists()
        ]
        if absents:
            avertissement(f"N={n} : graphiques absents : {absents}")
        else:
            ok(f"N={n} : les quatre graphiques sont présents.")

    afficher(erreurs, avertissements, controles)


def afficher(erreurs, avertissements, controles):
    print("\n========== BILAN DE VÉRIFICATION ==========\n")

    for message in controles:
        print(message)

    for message in avertissements:
        print(message)

    for message in erreurs:
        print(message)

    print("\n-------------------------------------------")
    print(f"Contrôles réussis : {len(controles)}")
    print(f"Avertissements   : {len(avertissements)}")
    print(f"Erreurs          : {len(erreurs)}")

    if erreurs:
        print("\nVERDICT : NE PAS VALIDER AVANT CORRECTION.")
    elif avertissements:
        print("\nVERDICT : données exploitables sous réserve "
              "de traiter les avertissements.")
    else:
        print("\nVERDICT : tous les contrôles automatisés sont réussis.")


if __name__ == "__main__":
    main()

