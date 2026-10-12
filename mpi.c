#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

static double *alloc_matrix(int n)
{
    double *m = malloc((size_t)n * n * sizeof(double));

    if (m == NULL)
    {
        fprintf(stderr, "Erreur : allocation memoire impossible.\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

    return m;
}

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

static void matmul_local(const double *A_local,
                         const double *BT,
                         double *C_local,
                         int local_rows,
                         int n)
{
    for (int i = 0; i < local_rows; i++)
    {
        for (int j = 0; j < n; j++)
        {
            double sum = 0.0;

            for (int k = 0; k < n; k++)
            {
                sum += A_local[i * n + k] * BT[j * n + k];
            }

            C_local[i * n + j] = sum;
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
    int rank, size;

    MPI_Init(&argc, &argv);

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int n = (argc > 1) ? atoi(argv[1]) : 1000;

    if (n <= 0)
    {
        if (rank == 0)
        {
            fprintf(stderr,
                    "Erreur : N doit etre strictement positif.\n");
        }

        MPI_Finalize();
        return EXIT_FAILURE;
    }

    if (n % size != 0)
    {
        if (rank == 0)
        {
            fprintf(stderr,
                    "Erreur : N=%d doit etre divisible par "
                    "le nombre de processus=%d.\n",
                    n, size);
        }

        MPI_Finalize();
        return EXIT_FAILURE;
    }

    /*
     * Debut du temps total.
     * MPI_Init et les verifications initiales sont exclus.
     */
    double total_start = MPI_Wtime();

    int local_rows = n / size;

    double *A = NULL;
    double *B = NULL;
    double *BT = NULL;
    double *C = NULL;

    /*
     * Allocation et preparation des matrices.
     * Le processus 0 initialise les matrices completes.
     */
    if (rank == 0)
    {
        A = alloc_matrix(n);
        B = alloc_matrix(n);
        BT = alloc_matrix(n);
        C = alloc_matrix(n);

        init_random(A, n, 42);
        init_random(B, n, 123);

        transpose_matrix(B, BT, n);
    }
    else
    {
        BT = alloc_matrix(n);
    }

    /*
     * Chaque processus recoit une copie complete de BT.
     */
    MPI_Bcast(
        BT,
        n * n,
        MPI_DOUBLE,
        0,
        MPI_COMM_WORLD
    );

    /*
     * Allocation des matrices locales.
     */
    double *A_local = alloc_array((size_t)local_rows * n);
    double *C_local = alloc_array((size_t)local_rows * n);

    /*
     * Distribution des lignes de A.
     */
    MPI_Scatter(
        A,
        local_rows * n,
        MPI_DOUBLE,
        A_local,
        local_rows * n,
        MPI_DOUBLE,
        0,
        MPI_COMM_WORLD
    );

    /*
     * Synchronisation avant le calcul.
     */
    MPI_Barrier(MPI_COMM_WORLD);

    /*
     * Mesure du calcul seul.
     */
    double calc_start = MPI_Wtime();

    matmul_local(
        A_local,
        BT,
        C_local,
        local_rows,
        n
    );

    double calc_end = MPI_Wtime();
    double temps_calcul_local = calc_end - calc_start;

    /*
     * Rassemblement des resultats sur le processus 0.
     */
    MPI_Gather(
        C_local,
        local_rows * n,
        MPI_DOUBLE,
        C,
        local_rows * n,
        MPI_DOUBLE,
        0,
        MPI_COMM_WORLD
    );

    /*
     * Le checksum est inclus dans le temps total.
     */
    double check = 0.0;

    if (rank == 0)
    {
        check = checksum(C, n);
    }

    /*
     * Synchronisation avant la fin du temps total.
     */
    MPI_Barrier(MPI_COMM_WORLD);

    double total_end = MPI_Wtime();
    double temps_total_local = total_end - total_start;

    /*
     * Le temps global est le maximum des temps locaux.
     */
    double temps_calcul = 0.0;
    double temps_total = 0.0;

    MPI_Reduce(
        &temps_calcul_local,
        &temps_calcul,
        1,
        MPI_DOUBLE,
        MPI_MAX,
        0,
        MPI_COMM_WORLD
    );

    MPI_Reduce(
        &temps_total_local,
        &temps_total,
        1,
        MPI_DOUBLE,
        MPI_MAX,
        0,
        MPI_COMM_WORLD
    );

    if (rank == 0)
    {
        printf("============================================================\n");
        printf("             MULTIPLICATION MATRICIELLE                    \n");
        printf("                         MPI                                 \n");
        printf("============================================================\n");
        printf("  Taille de la matrice : %d x %d\n", n, n);
        printf("  Nombre de processus  : %d\n", size);
        printf("  Temps de calcul      : %.6f secondes\n", temps_calcul);
        printf("  Temps total          : %.6f secondes\n", temps_total);
        printf("  Somme de controle    : %.10f\n", check);
        printf("------------------------------------------------------------\n");
        printf("  Optimisation         : transposition de B\n");
        printf("  Parallelisation      : MPI\n");
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

