#include <stdio.h>
#include <stdlib.h>
#include <time.h>

/*
 * Allocation dynamique d'une matrice n x n.
 */
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

/*
 * Initialisation d'une matrice avec des valeurs
 * pseudo-aleatoires comprises entre 0 et 1.
 */
static void init_random(double *m, int n, unsigned int seed)
{
    srand(seed);

    for (int i = 0; i < n * n; i++)
    {
        m[i] = (double)rand() / RAND_MAX;
    }
}

/*
 * Multiplication matricielle séquentielle naïve :
 *
 * C = A x B
 *
 * C[i][j] = somme(A[i][k] * B[k][j])
 */
static void matmul_seq(const double *A,
                       const double *B,
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
                sum += A[i * n + k] * B[k * n + j];
            }

            C[i * n + j] = sum;
        }
    }
}

/*
 * Somme de contrôle du résultat.
 *
 * Elle permet de vérifier que le calcul
 * produit un résultat cohérent.
 */
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
    /*
     * Utilisation :
     *
     * ./seq_naive 1000
     *
     * Si aucune taille n'est fournie,
     * N = 1000.
     */
    int n = (argc > 1) ? atoi(argv[1]) : 1000;

    if (n <= 0)
    {
        fprintf(stderr, "Erreur : N doit etre strictement positif.\n");
        return EXIT_FAILURE;
    }

    double *A = alloc_matrix(n);
    double *B = alloc_matrix(n);
    double *C = alloc_matrix(n);

    /*
     * Initialisation reproductible.
     */
    init_random(A, n, 42);
    init_random(B, n, 123);

    /*
     * Mesure uniquement de la multiplication.
     */
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    matmul_seq(A, B, C, n);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed =
        (end.tv_sec - start.tv_sec)
        + (end.tv_nsec - start.tv_nsec) / 1e9;

    /*
     * Vérification du résultat.
     */
    double check = checksum(C, n);

    printf("============================================================\n");
    printf("          MULTIPLICATION MATRICIELLE SEQUENTIELLE          \n");
    printf("                     VERSION NAIVE                          \n");
    printf("============================================================\n");
    printf("  Taille de la matrice : %d x %d\n", n, n);
    printf("  Temps d'execution    : %.6f secondes\n", elapsed);
    printf("  Somme de controle    : %.10f\n", check);
    printf("------------------------------------------------------------\n");
    printf("  Statut               : EXECUTION TERMINEE\n");
    printf("============================================================\n");

    free(A);
    free(B);
    free(C);

    return EXIT_SUCCESS;
}
