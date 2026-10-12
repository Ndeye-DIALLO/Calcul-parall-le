# Étude des performances de la multiplication matricielle parallèle

## 1. Présentation du projet

Ce projet étudie les performances de la multiplication de matrices carrées à l'aide de plusieurs approches de calcul :

- **Séquentielle** : exécution classique sur un seul thread.
- **OpenMP** : parallélisation par threads au sein d'un processus.
- **MPI** : parallélisation à l'aide de plusieurs processus.
- **Configurations supplémentaires** : comparaison de configurations utilisant un processus avec quatre threads ou quatre processus avec un thread chacun.

L'objectif est de comparer les temps de calcul, les accélérations et les efficacités obtenus pour différentes tailles de matrices.

## 2. Environnement expérimental

Les expériences ont été réalisées sur une machine équipée d'un processeur Intel Core i5-7300U, disposant de deux cœurs physiques, de quatre processeurs logiques et d'environ 3,7 Gio de mémoire vive disponible.

Les tailles de matrices étudiées sont :

- N = 500
- N = 1000
- N = 1500
- N = 2000

Cinq configurations ont été comparées pour chaque taille. Les mesures comprennent cinq répétitions pour N = 500, N = 1000 et N = 2000, et dix répétitions pour N = 1500.

Au total, 125 mesures expérimentales ont été enregistrées.

## 3. Organisation des fichiers

Le projet contient notamment les fichiers suivants :

| Fichier | Description |
|---|---|
| `séq.c` | Code source de la version séquentielle |
| `séq_optimisé.c` | Code source de la version séquentielle optimisée |
| `openmp.c` | Code source utilisant OpenMP |
| `mpi.c` | Code source utilisant MPI |
| `hybride.c` | Code source associé aux configurations supplémentaires |
| `collecter.py` | Script de collecte des résultats |
| `analyser.py` | Script d'analyse des mesures et de génération des graphiques |
| `verifier_final.py` | Script de vérification des résultats |
| `resultats.csv` | Données expérimentales |
| `resultats_bruts.txt` | Résultats bruts des expériences |
| `statistiques.csv` | Statistiques calculées à partir des mesures |
| `resultats_backup.csv` | Copie de sauvegarde des résultats |
| `rapport_calculmatricielle.tex` | Source LaTeX du rapport |
| `README.md` | Documentation du projet |

Les graphiques générés présentent les temps de calcul, les temps totaux, les accélérations et les efficacités pour les différentes tailles de matrices.

## 4. Prérequis

Pour compiler et exécuter les programmes, les outils suivants peuvent être nécessaires :

- un compilateur C, par exemple GCC ;
- OpenMP, généralement disponible avec GCC ;
- une implémentation MPI, par exemple Open MPI ;
- Python 3 ;
- les bibliothèques Python nécessaires à l'analyse, notamment Matplotlib.

Les commandes suivantes permettent de vérifier certains outils sous Linux :

```bash
gcc --version
mpicc --version
mpirun --version
python3 --version
```

## 5. Compilation des programmes

Depuis le répertoire du projet, les commandes de compilation usuelles sont :

### Version séquentielle

```bash
gcc -O2 séq.c -o séq
```

### Version séquentielle optimisée

```bash
gcc -O2 séq_optimisé.c -o séq_optimisé
```

### Version OpenMP

```bash
gcc -O2 -fopenmp openmp.c -o openmp
```

### Version MPI

```bash
mpicc -O2 mpi.c -o mpi
```

### Programme associé aux configurations supplémentaires

Si le code utilise effectivement MPI et OpenMP, il peut être compilé avec :

```bash
mpicc -O2 -fopenmp hybride.c -o hybride
```

La compilation doit être adaptée si les sources utilisent d'autres bibliothèques ou options. Les noms des exécutables produits doivent correspondre aux commandes utilisées ensuite.

## 6. Exécution

Les exemples ci-dessous supposent que les programmes utilisent des paramètres définis dans le code. Si la taille de matrice est fournie en argument, il faut adapter les commandes à l'interface réelle du programme.

### Version séquentielle

```bash
./séq
```

### Version OpenMP avec quatre threads

```bash
OMP_NUM_THREADS=4 ./openmp
```

### Version MPI avec quatre processus

```bash
mpirun -np 4 ./mpi
```

### Configurations supplémentaires

Un processus avec quatre threads OpenMP :

```bash
OMP_NUM_THREADS=4 ./hybride
```

Quatre processus avec un thread chacun :

```bash
OMP_NUM_THREADS=1 mpirun -np 4 ./hybride
```

Ces deux dernières commandes ne représentent une configuration hybride que si le programme combine réellement MPI et OpenMP. Dans les expériences présentées, les configurations comparées correspondent à un processus avec quatre threads ou à quatre processus avec un thread chacun. Elles ne testent donc pas encore plusieurs processus MPI exécutant chacun plusieurs threads OpenMP.

## 7. Analyse et vérification des résultats

Le script `analyser.py` permet d'exploiter les mesures et de générer des statistiques ainsi que des graphiques.

Si l'environnement virtuel Python du projet est disponible, l'analyse peut être lancée avec :

```bash
.venv/bin/python analyser.py
```

La vérification des résultats peut être exécutée avec :

```bash
.venv/bin/python verifier_final.py
```

Les scripts doivent être exécutés depuis le répertoire du projet. Ils peuvent nécessiter des dépendances Python déjà installées dans l'environnement virtuel.

Le fichier `resultats.csv` contient les mesures expérimentales. Le fichier `statistiques.csv` contient les statistiques calculées. Les graphiques permettent de visualiser l'évolution des performances en fonction de la taille des matrices et de la configuration.

## 8. Indicateurs utilisés

L'accélération est définie par :

\[
S_p = \frac{T_{\mathrm{seq}}}{T_p}
\]

où \(T_{\mathrm{seq}}\) est le temps moyen de la version séquentielle et \(T_p\) celui de la configuration étudiée.

L'efficacité conventionnelle est définie par :

\[
E_p = \frac{S_p}{P}\times100\%
\]

où \(P\) désigne le nombre de travailleurs configurés selon la convention retenue dans le projet.

Les temps de calcul et les temps totaux sont deux mesures distinctes. Le rapport précise la mesure utilisée pour les comparaisons.

## 9. Résultats principaux

Les mesures montrent que les configurations parallèles testées sont plus rapides que la version séquentielle pour les tailles étudiées.

OpenMP et la configuration à un processus avec quatre threads obtiennent généralement les meilleurs temps. Les performances de MPI sont également supérieures à celles de la version séquentielle, mais elles sont généralement moins bonnes que celles des configurations à quatre threads sur la machine testée.

Ces résultats dépendent du matériel, de l'implémentation et des conditions d'exécution. Ils ne permettent pas, à eux seuls, d'isoler les coûts de communication, de synchronisation ou d'accès mémoire.

## 10. Rapport et graphiques

Le rapport complet est disponible dans `rapport_calculmatricielle.tex`. Après compilation avec LaTeX, il produit le document PDF.

Les graphiques détaillés sont conservés dans le dossier du projet. Ils présentent notamment les temps de calcul, les temps totaux, les accélérations et les efficacités pour les tailles N = 500, 1000, 1500 et 2000.

Ils complètent les tableaux et l'analyse du rapport et permettent d'examiner plus précisément les résultats expérimentaux.

## 11. Perspectives

Les améliorations possibles comprennent :

- tester une véritable combinaison MPI et OpenMP ;
- augmenter le nombre de répétitions expérimentales ;
- contrôler davantage la charge du système pendant les mesures ;
- comparer les résultats sur une machine disposant de davantage de cœurs physiques ;
- étudier séparément les coûts de calcul, de communication et de synchronisation.

---

**Fin du README.**
