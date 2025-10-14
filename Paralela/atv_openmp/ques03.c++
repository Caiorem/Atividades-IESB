/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 14/10/2025

Questão 03:

Exercício 3 — Expressão Vetorial
Implemente a expressão: a[i] = x[i]^2 + y[i]^2 + z[i]^2 para vetores de tamanho 1.000.000.
a) Faça a versão sequencial.
b) Paralelize com #pragma omp parallel for schedule(static).
c) Mostre o tempo total de execução em cada versão.

*******************************************************************************/

#include <iostream>
#include <vector>      // Para usar vetores dinâmicos (heap)
#include <cmath>       // Para a função pow()
#include <iomanip>     // Para formatar a saída de tempo
#include <omp.h>

int main(){

    const long long TAMANHO = 1000000;

    // --- CORREÇÃO 1: Usar std::vector para alocar na HEAP e evitar estouro de memória ---
    // Usaremos 'double' para evitar overflow com números grandes ao quadrado.
    std::vector<double> a(TAMANHO);
    std::vector<double> x(TAMANHO, 2.0); // Inicializa todos os elementos com 2.0
    std::vector<double> y(TAMANHO, 3.0); // Inicializa todos os elementos com 3.0
    std::vector<double> z(TAMANHO, 4.0); // Inicializa todos os elementos com 4.0
    
    std::cout << "Calculando expressao para " << TAMANHO << " elementos..." << std::endl << std::endl;

    // a) Versão sequencial com medição de tempo
    double start_seq = omp_get_wtime();
    
    for(long long i = 0; i < TAMANHO; i++){
        // --- CORREÇÃO 2: Armazenar o resultado em a[i] ---
        // pow(base, expoente) calcula a potência. Ex: pow(x[i], 2) é x[i]^2
        a[i] = pow(x[i], 2) + pow(y[i], 2) + pow(z[i], 2);
    }

    double end_seq = omp_get_wtime();
    double tempo_seq = end_seq - start_seq;

    std::cout << "--- Versao Sequencial ---" << std::endl;
    std::cout << "Tempo de execucao: " << std::fixed << std::setprecision(5) << tempo_seq << " segundos." << std::endl;
    // Checando um valor para garantir que o cálculo foi feito
    std::cout << "Valor de a[ultimo] = " << a[TAMANHO - 1] << " (Esperado: 4+9+16=29)" << std::endl;
    std::cout << std::endl;


    // b) Versão paralela com medição de tempo
    double start_par = omp_get_wtime();
    
    #pragma omp parallel for schedule(static)
    for(long long i = 0; i < TAMANHO; i++){
        a[i] = pow(x[i], 2) + pow(y[i], 2) + pow(z[i], 2);
    }
    
    double end_par = omp_get_wtime();
    double tempo_par = end_par - start_par;
    
    std::cout << "--- Versao Paralela com schedule(static) ---" << std::endl;
    std::cout << "Tempo de execucao: " << std::fixed << std::setprecision(5) << tempo_par << " segundos." << std::endl;
    std::cout << "Valor de a[ultimo] = " << a[TAMANHO - 1] << " (Esperado: 29)" << std::endl;
    std::cout << std::endl;

    // c) Comparação final
    std::cout << "--- Comparacao Final ---" << std::endl;
    if (tempo_par > 0) {
        double speedup = tempo_seq / tempo_par;
        std::cout << "A versao paralela foi " << std::fixed << std::setprecision(2) << speedup << " vezes mais rapida." << std::endl;
    }

    return 0;
}