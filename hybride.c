#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <mpi.h>

static double *alloc_array(size_t count)
{
    double *m = malloc(count * sizeof(double));

    if (m == NULL)
    {
        fprintf(stderr, "Erreur : allocation memoire impossible.\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    return m;
}

static double *alloc_matrix(int n)
{
    return alloc_array((size_t)n * n);
}

static void init_random(double *m, int n, unsigned int seed)
{
    srand(seed);

    for (size_t i = 0; i < (size_t)n * n; i++)
        m[i] = (double)rand() / RAND_MAX;
}

static void transpose_matrix(const double *B, double *BT, int n)
{
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            BT[(size_t)j * n + i] = B[(size_t)i * n + j];
}

static void matmul_hybrid(const double *A_local,
                          const double *BT,
                          double *C_local,
                          int local_rows,
                          int n)
{
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < local_rows; i++)
    {
        for (int j = 0; j < n; j++)
        {
            double sum = 0.0;

            for (int k = 0; k < n; k++)
                sum += A_local[(size_t)i * n + k]
                     * BT[(size_t)j * n + k];

            C_local[(size_t)i * n + j] = sum;
        }
    }
}

static double checksum(const double *C, int n)
{
    double sum = 0.0;

    for (size_t i = 0; i < (size_t)n * n; i++)
        sum += C[i];

    return sum;
}

int main(int argc, char *argv[])
{
    int rank, size;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int n = (argc > 1) ? atoi(argv[1]) : 1000;

    if (n <= 0 || n % size != 0)
    {
        if (rank == 0)
            fprintf(stderr,
                    "Erreur : N doit etre positif et divisible "
                    "par le nombre de processus.\n");

        MPI_Finalize();
        return EXIT_FAILURE;
    }

    int local_rows = n / size;
    int threads = 1;

    double *A = NULL;
    double *B = NULL;
    double *C = NULL;
    double *BT = NULL;
    double *A_local = NULL;
    double *C_local = NULL;

    /* Synchroniser les processus avant le chronometrage total. */
    MPI_Barrier(MPI_COMM_WORLD);
    double total_start = MPI_Wtime();

    /* Allocation et preparation des matrices. */
    BT = alloc_matrix(n);

    if (rank == 0)
    {
        A = alloc_matrix(n);
        B = alloc_matrix(n);
        C = alloc_matrix(n);

        init_random(A, n, 42);
        init_random(B, n, 123);
        transpose_matrix(B, BT, n);
    }

    MPI_Bcast(BT, n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    A_local = alloc_array((size_t)local_rows * n);
    C_local = alloc_array((size_t)local_rows * n);

    MPI_Scatter(A, local_rows * n, MPI_DOUBLE,
                A_local, local_rows * n, MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    /* Relever le nombre reel de threads dans la region OpenMP. */
    #pragma omp parallel
    {
        #pragma omp single
        threads = omp_get_num_threads();
    }

    /* Mesure du calcul seul, hors communications MPI. */
    MPI_Barrier(MPI_COMM_WORLD);
    double calc_start = MPI_Wtime();

    matmul_hybrid(A_local, BT, C_local, local_rows, n);

    double calc_end = MPI_Wtime();
    double calc_local = calc_end - calc_start;

    /* Rassembler les blocs de la matrice resultat. */
    MPI_Gather(C_local, local_rows * n, MPI_DOUBLE,
               C, local_rows * n, MPI_DOUBLE,
               0, MPI_COMM_WORLD);

    double check = 0.0;

    if (rank == 0)
        check = checksum(C, n);

    /* Inclure le rassemblement et la somme de controle au total. */
    MPI_Barrier(MPI_COMM_WORLD);
    double total_end = MPI_Wtime();
    double total_local = total_end - total_start;

    /* Le temps global est le maximum parmi les processus. */
    double calc_max = 0.0;
    double total_max = 0.0;

    MPI_Reduce(&calc_local, &calc_max, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    MPI_Reduce(&total_local, &total_max, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0)
    {
        printf("============================================================\n");
        printf("             MULTIPLICATION MATRICIELLE\n");
        printf("                      MPI + OpenMP\n");
        printf("============================================================\n");
        printf("  Taille de la matrice : %d x %d\n", n, n);
        printf("  Nombre de processus  : %d\n", size);
        printf("  Threads par processus: %d\n", threads);
        printf("  Temps de calcul      : %.6f secondes\n", calc_max);
        printf("  Temps total          : %.6f secondes\n", total_max);
        printf("  Somme de controle    : %.10f\n", check);
        printf("------------------------------------------------------------\n");
        printf("  Optimisation         : transposition de B\n");
        printf("  Parallelisation      : MPI + OpenMP\n");
        printf("  Statut               : EXECUTION TERMINEE\n");
        printf("============================================================");
        printf("\n");
    }

    free(A_local);
    free(C_local);
    free(BT);

    if (rank == 0)
    {
        free(A);
        free(B);
        free(C);
    }

    MPI_Finalize();
    return EXIT_SUCCESS;
}

