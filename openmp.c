#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

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

static void matmul_openmp(const double *A,
                          const double *BT,
                          double *C,
                          int n)
{
    #pragma omp parallel for schedule(static)
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

    double total_start = omp_get_wtime();

    double *A = alloc_matrix(n);
    double *B = alloc_matrix(n);
    double *BT = alloc_matrix(n);
    double *C = alloc_matrix(n);

    init_random(A, n, 42);
    init_random(B, n, 123);

    transpose_matrix(B, BT, n);

    int threads = 1;
    double calc_start = omp_get_wtime();

    #pragma omp parallel
    {
        #pragma omp single
        threads = omp_get_num_threads();
    }

    /* La mesure de calcul inclut la multiplication OpenMP. */
    calc_start = omp_get_wtime();
    matmul_openmp(A, BT, C, n);
    double calc_end = omp_get_wtime();

    double check = checksum(C, n);

    double total_end = omp_get_wtime();

    double temps_calcul = calc_end - calc_start;
    double temps_total = total_end - total_start;

    printf("============================================================\n");
    printf("             MULTIPLICATION MATRICIELLE                    \n");
    printf("                       OPENMP                               \n");
    printf("============================================================\n");
    printf("  Taille de la matrice : %d x %d\n", n, n);
    printf("  Threads utilises     : %d\n", threads);
    printf("  Temps de calcul      : %.6f secondes\n", temps_calcul);
    printf("  Temps total          : %.6f secondes\n", temps_total);
    printf("  Somme de controle    : %.10f\n", check);
    printf("------------------------------------------------------------\n");
    printf("  Optimisation         : transposition de B\n");
    printf("  Parallelisation      : OpenMP\n");
    printf("  Statut               : EXECUTION TERMINEE\n");
    printf("============================================================\n");

    free(A);
    free(B);
    free(BT);
    free(C);

    return EXIT_SUCCESS;
}

  
   
