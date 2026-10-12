
import csv
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

RACINE = Path(__file__).resolve().parent
FICHIER_CSV = RACINE / "resultats.csv"

TAILLES = [500, 1000, 1500, 2000]
REPETITIONS = 5

# Les commandes reçoivent la taille en argument.
CONFIGURATIONS = [
    {
        "version": "seq",
        "mpi": 1,
        "omp": 1,
        "commande": lambda n: ["./séq_optimisé", str(n)],
        "env": {},
    },
    {
        "version": "omp",
        "mpi": 1,
        "omp": 4,
        "commande": lambda n: ["./openmp", str(n)],
        "env": {"OMP_NUM_THREADS": "4"},
    },
    {
        "version": "mpi",
        "mpi": 4,
        "omp": 1,
        "commande": lambda n: [
            "mpirun", "--bind-to", "none",
            "--use-hwthread-cpus", "-np", "4",
            "./mpi", str(n)
        ],
        "env": {},
    },
    {
        "version": "hybride",
        "mpi": 1,
        "omp": 4,
        "commande": lambda n: [
            "mpirun", "--bind-to", "none",
            "--use-hwthread-cpus", "-np", "1",
            "./hybride", str(n)
        ],
        "env": {"OMP_NUM_THREADS": "4"},
    },
    {
        "version": "hybride",
        "mpi": 4,
        "omp": 1,
        "commande": lambda n: [
            "mpirun", "--bind-to", "none",
            "--use-hwthread-cpus", "-np", "4",
            "./hybride", str(n)
        ],
        "env": {"OMP_NUM_THREADS": "1"},
    },
]

COLONNES = [
    "date", "version", "processus_mpi", "threads_omp",
    "essai", "taille", "calcul_s", "total_s", "checksum"
]


def extraire(nom, texte):
    motif = rf"{re.escape(nom)}\s*:\s*([0-9]+(?:\.[0-9]+)?)"
    resultat = re.search(motif, texte, re.IGNORECASE)
    if not resultat:
        raise ValueError(f"Valeur '{nom}' introuvable dans la sortie :\n{texte}")
    return float(resultat.group(1))


def main():
    FICHIER_CSV.parent.mkdir(parents=True, exist_ok=True)
    fichier_existe = (
        FICHIER_CSV.exists() and FICHIER_CSV.stat().st_size > 0
    )

    with FICHIER_CSV.open("a", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=COLONNES)

        if not fichier_existe:
            writer.writeheader()

        for taille in TAILLES:
            for config in CONFIGURATIONS:
                for essai in range(1, REPETITIONS + 1):
                    commande = config["commande"](taille)

                    environnement = os.environ.copy()
                    environnement.update(config["env"])

                    print(
                        f"N={taille} | Version={config['version']} "
                        f"| MPI={config['mpi']} | OMP={config['omp']} "
                        f"| essai={essai}/{REPETITIONS}",
                        flush=True,
                    )

                    execution = subprocess.run(
                        commande,
                        cwd=RACINE,
                        env=environnement,
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    sortie = execution.stdout
                    calcul = extraire("Temps de calcul", sortie)
                    total = extraire("Temps total", sortie)
                    checksum = extraire("Somme de controle", sortie)

                    writer.writerow({
                        "date": datetime.now().isoformat(timespec="seconds"),
                        "version": config["version"],
                        "processus_mpi": config["mpi"],
                        "threads_omp": config["omp"],
                        "essai": essai,
                        "taille": taille,
                        "calcul_s": calcul,
                        "total_s": total,
                        "checksum": checksum,
                    })
                    fichier.flush()

    print(f"\nRésultats enregistrés dans : {FICHIER_CSV}")


if __name__ == "__main__":
    main()

