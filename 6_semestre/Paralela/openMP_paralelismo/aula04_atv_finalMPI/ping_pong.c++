// Exercício 1: Ping-Pong com MPI
// Objetivo: realizar 10 trocas (envios) alternados entre dois processos.

// Cada envio transmite um inteiro que começa em 0 e é incrementado a cada vez.
// Processo 0 envia primeiro; processo 1 recebe e devolve; isso continua até o valor 9.

#include <iostream>
#include <mpi.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Exige exatamente 2 processos
    if (size != 2) {
        if (rank == 0) {
            std::cerr << "Erro: este programa deve ser executado com exatamente 2 processos." << std::endl;
        }
        MPI_Finalize();
        return 1;
    }

    const int NUM_TROCAS = 10;  // número total de envios (send)
    const int TAG = 0;
    MPI_Status status;

    int valor;

    if (rank == 0) {
        // Processo 0 inicia o ping enviando o valor 0
        valor = 0;
        MPI_Send(&valor, 1, MPI_INT, 1, TAG, MPI_COMM_WORLD);
        std::cout << "Processo 0 enviou " << valor << std::endl;

        // Já houve 1 envio, faltam NUM_TROCAS - 1
        for (int i = 1; i < NUM_TROCAS; i++) {
            // 1) recebe do processo 1
            MPI_Recv(&valor, 1, MPI_INT, 1, TAG, MPI_COMM_WORLD, &status);
            std::cout << "Processo 0 recebeu " << valor << std::endl;

            // Se já atingimos o número total de trocas, parar
            if (i == NUM_TROCAS - 1)
                break;

            // 2) incrementa e envia de volta
            valor++;
            MPI_Send(&valor, 1, MPI_INT, 1, TAG, MPI_COMM_WORLD);
            std::cout << "Processo 0 enviou " << valor << std::endl;
        }

        std::cout << "Processo 0 finalizando." << std::endl;
    }
    else {
        // Processo 1 apenas responde cada valor até completar NUM_TROCAS
        for (int i = 0; i < NUM_TROCAS; i++) {
            // 1) recebe de P0
            MPI_Recv(&valor, 1, MPI_INT, 0, TAG, MPI_COMM_WORLD, &status);
            std::cout << "Processo 1 recebeu " << valor << std::endl;

            // Se for a última troca, não retorna nada
            if (i == NUM_TROCAS - 1)
                break;

            // 2) incrementa e envia de volta
            valor++;
            MPI_Send(&valor, 1, MPI_INT, 0, TAG, MPI_COMM_WORLD);
            std::cout << "Processo 1 enviou " << valor << std::endl;
        }

        std::cout << "Processo 1 finalizando." << std::endl;
    }

    MPI_Finalize();
    return 0;
}
