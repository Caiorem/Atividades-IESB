/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 14/10/2025

Questão 04:

Exercício 4 — Medindo tempo por thread
Adapte o código do exercício anterior para:
a) Medir e exibir o tempo total de execução.
b) Medir e exibir o tempo gasto por cada thread.
c) Mostrar quantas threads foram utilizadas no cálculo.

*******************************************************************************/

#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <omp.h>

int main(){
    // Define o tamanho dos vetores para um trabalho computacionalmente relevante.
    const long long TAMANHO = 10000000; // Aumentado para 10 milhões para a medição ser mais clara

    // Aloca os vetores na memória Heap usando std::vector para evitar estouro de memória.
    std::vector<double> a(TAMANHO);
    std::vector<double> x(TAMANHO, 2.0);
    std::vector<double> y(TAMANHO, 3.0);
    std::vector<double> z(TAMANHO, 4.0);
    
    // Prepara um vetor para armazenar o tempo de execução de cada thread.
    // O tamanho é baseado no máximo de threads que o OpenMP pode criar.
    int max_threads = omp_get_max_threads();
    std::vector<double> tempos_threads(max_threads, 0.0);
    int threads_utilizadas = 0;

    // Mede o tempo de início da execução total.
    double tempo_total_inicio = omp_get_wtime();

    // Inicia a região paralela. A partir daqui, o código será executado por múltiplos threads.
    #pragma omp parallel
    {
        // Cada thread obtém seu número de identificação (ID).
        int thread_id = omp_get_thread_num();

        // A diretiva 'single' garante que o bloco de código seguinte
        // seja executado por apenas UM thread, evitando que a variável
        // 'threads_utilizadas' seja escrita por todos ao mesmo tempo.
        #pragma omp single
        {
            threads_utilizadas = omp_get_num_threads();
        }

        // Cada thread registra seu próprio tempo de início.
        double tempo_thread_inicio = omp_get_wtime();

        // O trabalho do laço 'for' é dividido entre os threads disponíveis.
        #pragma omp for
        for(long long i = 0; i < TAMANHO; i++){
            a[i] = pow(x[i], 2) + pow(y[i], 2) + pow(z[i], 2);
        }

        // Após terminar sua parte do trabalho, cada thread registra seu tempo de fim.
        double tempo_thread_fim = omp_get_wtime();

        // A duração é calculada e armazenada na posição correspondente ao ID do thread.
        tempos_threads[thread_id] = tempo_thread_fim - tempo_thread_inicio;
    }
    // Fim da região paralela. O código volta a ser executado por um único thread.

    // Mede o tempo de fim da execução total.
    double tempo_total_fim = omp_get_wtime();
    double tempo_total = tempo_total_fim - tempo_total_inicio;


    // --- Apresentação dos Resultados ---
    
    // Configura a formatação para exibir números com 5 casas decimais.
    std::cout << std::fixed << std::setprecision(5);

    // a) Exibe o tempo total de execução.
    std::cout << "a) Tempo total de execucao: " << tempo_total << " segundos." << std::endl;
    std::cout << std::endl;

    // b) Exibe o tempo gasto por cada thread individualmente.
    std::cout << "b) Tempo gasto por cada thread:" << std::endl;
    for (int i = 0; i < threads_utilizadas; ++i) {
        std::cout << "   - Thread " << i << ": " << tempos_threads[i] << " segundos." << std::endl;
   }

    // c) Mostra quantas threads foram utilizadas.
    std::cout << std::endl;
    std::cout << "c) Total de threads utilizadas no calculo: " << threads_utilizadas << std::endl;
    std::cout << std::endl;
 
    return 0;
}