#include <iostream>
#include <vector>
#include <numeric> // Para std::accumulate
#include <mpi.h>

int main(int argc, char** argv) {
    // Inicializa o ambiente MPI
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); // Obtém o identificador do processo (rank)
    MPI_Comm_size(MPI_COMM_WORLD, &size); // Obtém o número total de processos

    // Verifica se há pelo menos 2 processos (1 Mestre + 1 Trabalhador)
    if (size < 2) {
        if (rank == 0) 
            std::cerr << "Erro: Requer pelo menos 2 processos." << std::endl;
        MPI_Finalize();
        return 1;
    }

    const int TAMANHO_TOTAL = 1200;
    int num_trabalhadores = size - 1; // Número de processos trabalhadores

    if (rank == 0) {
        // ==================================================
        // LÓGICA DO MESTRE (Processo 0)
        // ==================================================

        // Verifica se o vetor pode ser dividido igualmente entre os trabalhadores
        if (TAMANHO_TOTAL % num_trabalhadores != 0) {
            std::cerr << "Erro: O tamanho do vetor nao e divisivel pelo numero de trabalhadores." << std::endl;
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        // 1. Cria e preenche o vetor com 1s
        std::vector<int> vetor_mestre(TAMANHO_TOTAL, 1);
        int tamanho_parte = TAMANHO_TOTAL / num_trabalhadores;
        int soma_total = 0;

        std::cout << "Mestre (P0): Dividindo o trabalho para " << num_trabalhadores << " trabalhadores." << std::endl;

        // 2. Enviar partes do vetor para cada trabalhador
        for (int i = 1; i < size; i++) {
            int indice_inicial = (i - 1) * tamanho_parte;
            
            // Envia uma fatia do vetor para o trabalhador 'i'
            MPI_Send(&vetor_mestre[indice_inicial], tamanho_parte, MPI_INT, i, 0, MPI_COMM_WORLD);
        }

        // 3. Receber resultados parciais dos trabalhadores
        for (int i = 1; i < size; i++) {
            int soma_parcial = 0;
            MPI_Recv(&soma_parcial, 1, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            soma_total += soma_parcial;
        }

        std::cout << "Mestre (P0): Soma total = " << soma_total << std::endl;

    } else {
        // ==================================================
        // LÓGICA DOS TRABALHADORES (rank != 0)
        // ==================================================

        int tamanho_parte = TAMANHO_TOTAL / num_trabalhadores;
        std::vector<int> parte(tamanho_parte);

        // Recebe a fatia enviada pelo mestre
        MPI_Recv(parte.data(), tamanho_parte, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

        // Calcula a soma da fatia
        int soma_parcial = std::accumulate(parte.begin(), parte.end(), 0);

        std::cout << "Trabalhador (P" << rank << "): soma parcial = " << soma_parcial << std::endl;

        // Envia a soma parcial de volta ao mestre
        MPI_Send(&soma_parcial, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }

    // Finaliza o ambiente MPI
    MPI_Finalize();
    return 0;
}
