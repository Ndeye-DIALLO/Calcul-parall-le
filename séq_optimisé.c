#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double *alloc_matrix(int n)
{
    double *m = malloc((size_t)n * n * sizeof(double));

    if (m == NULL)
    {
        fprintf(stderr, "Erreur : allocation memoire impossible.\n");
        exit(EXIT_FAILURE);
    }

    return m;
}

static void init_random(double *m, int n, unsigned int seed)
{
    srand(seed);

    for (int i = 0; i < n * n; i++)
    {
        m[i] = (double)rand() / RAND_MAX;
    }
}

/*
 * Transpose B :
 *
 * B[i][j] devient BT[j][i]
 */
static void transpose_matrix(const double *B, double *BT, int n)
{
    for (int i = 0; i < n; i++)
    {
        for (int j = 0; j < n; j++)
        {
            BT[j * n + i] = B[i * n + j];
        }
    }
}

/*
 * Multiplication :
 *
 * C = A x B
 *
 * Mais on utilise BT pour améliorer les accès mémoire.
 */
static void matmul_transposed(const double *A,
                              const double *BT,
                              double *C,
                              int n)
{
    for (int i = 0; i < n; i++)
    {
        for (int j = 0; j < n; j++)
        {
            double sum = 0.0;

            for (int k = 0; k < n; k++)
            {
                sum += A[i * n + k] * BT[j * n + k];
            }

            C[i * n + j] = sum;
        }
    }
}

static double checksum(const double *C, int n)
{
    double sum = 0.0;

    for (int i = 0; i < n * n; i++)
    {
        sum += C[i];
    }

    return sum;
}


int main(int argc, char *argv[])
{
    int n = (argc > 1) ? atoi(argv[1]) : 1000;

    if (n <= 0)
    {
        fprintf(stderr, "Erreur : N doit etre strictement positif.\n");
        return EXIT_FAILURE;
    }

    struct timespec total_start, calc_start, calc_end, total_end;

    /* Debut de la mesure totale : avant les allocations */
    clock_gettime(CLOCK_MONOTONIC, &total_start);

    double *A = alloc_matrix(n);
    double *B = alloc_matrix(n);
    double *BT = alloc_matrix(n);
    double *C = alloc_matrix(n);

    /* Initialisation des matrices */
    init_random(A, n, 42);
    init_random(B, n, 123);

    /* Transposition de B */
    transpose_matrix(B, BT, n);

    /* Mesure du calcul seul */
    clock_gettime(CLOCK_MONOTONIC, &calc_start);

    matmul_transposed(A, BT, C, n);

    clock_gettime(CLOCK_MONOTONIC, &calc_end);

    /* Verification du resultat */
    double check = checksum(C, n);

    /* Fin de la mesure totale */
    clock_gettime(CLOCK_MONOTONIC, &total_end);

    double temps_calcul =
        (calc_end.tv_sec - calc_start.tv_sec)
        + (calc_end.tv_nsec - calc_start.tv_nsec) / 1e9;

    double temps_total =
        (total_end.tv_sec - total_start.tv_sec)
        + (total_end.tv_nsec - total_start.tv_nsec) / 1e9;

    printf("============================================================\n");
    printf("       MULTIPLICATION MATRICIELLE SEQUENTIELLE             \n");
    printf("              VERSION AVEC TRANSPOSEE                       \n");
    printf("============================================================\n");
    printf("  Taille de la matrice : %d x %d\n", n, n);
    printf("  Temps de calcul      : %.6f secondes\n", temps_calcul);
    printf("  Temps total          : %.6f secondes\n", temps_total);
    printf("  Somme de controle    : %.10f\n", check);
    printf("------------------------------------------------------------\n");
    printf("  Optimisation         : transposition de B\n");
    printf("  Statut               : EXECUTION TERMINEE\n");
    printf("============================================================\n");

    free(A);
    free(B);
    free(BT);
    free(C);

    return EXIT_SUCCESS;
}

