/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 14/10/2025

Questão 05:

Exercício 5 — Escalonamento
Use novamente o cálculo de a[i] = x[i]^2 + y[i]^2 + z[i]^2, mas:
a) Execute com schedule(static) e schedule(dynamic, 1000).
b) Compare os tempos em diferentes quantidades de threads (2, 4, 8).
c) Explique em quais situações static e dynamic são mais adequados.

*******************************************************************************/

#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <omp.h>

// Uma função auxiliar para executar e medir o cálculo, evitando repetição de código.
void executarCalculo(long long tamanho, const std::vector<double>& x, const std::vector<double>& y, const std::vector<double>& z, std::vector<double>& a, const std::string& tipo_schedule) {
    
    double tempo_inicio = omp_get_wtime();

    if (tipo_schedule == "static") {
        #pragma omp parallel for schedule(static)
        for(long long i = 0; i < tamanho; i++){
            a[i] = pow(x[i], 2) + pow(y[i], 2) + pow(z[i], 2);
        }
    } else if (tipo_schedule == "dynamic") {
        // Usa um chunk (bloco) de 1000 iterações, como pedido no exercício.
        #pragma omp parallel for schedule(dynamic, 1000)
        for(long long i = 0; i < tamanho; i++){
            a[i] = pow(x[i], 2) + pow(y[i], 2) + pow(z[i], 2);
        }
    }
    
    double tempo_fim = omp_get_wtime();
    double duracao = tempo_fim - tempo_inicio;

    std::cout << "   - Tempo com schedule(" << tipo_schedule << "): \t" << std::fixed << std::setprecision(5) << duracao << " segundos." << std::endl;
}

int main(){
    const long long TAMANHO = 20000000; // 20 milhões de elementos

    // Alocação e inicialização dos vetores na memória Heap.
    std::vector<double> a(TAMANHO);
    std::vector<double> x(TAMANHO, 2.0);
    std::vector<double> y(TAMANHO, 3.0);
    std::vector<double> z(TAMANHO, 4.0);
    
    // b) Vetor com as contagens de threads para testar.
    std::vector<int> contagem_threads = {2, 4, 8};

    std::cout << "Iniciando comparacao de escalonamento para " << TAMANHO << " elementos..." << std::endl << std::endl;

    for (int n_threads : contagem_threads) {
        std::cout << "--- Executando com " << n_threads << " threads ---" << std::endl;

        // Define o número de threads para as próximas regiões paralelas.
        omp_set_num_threads(n_threads);

        // a) Executa e mede o tempo para cada tipo de escalonamento.
        executarCalculo(TAMANHO, x, y, z, a, "static");
        executarCalculo(TAMANHO, x, y, z, a, "dynamic");
        
        std::cout << std::endl;
    }

    // c) Explicação sobre as políticas de escalonamento.
    std::cout << "--- c) Explicacao sobre Static vs. Dynamic ---" << std::endl << std::endl;
    std::cout << "Em qual situacao cada tipo de escalonamento e mais adequado?" << std::endl << std::endl;
    
    std::cout << "1. schedule(static):" << std::endl;
    std::cout << "   - Como funciona: O OpenMP divide as iteracoes em blocos de tamanho praticamente igual e entrega um bloco para cada thread ANTES do loop comecar. A distribuicao e fixa." << std::endl;
    std::cout << "   - Quando usar: E ideal para loops onde CADA ITERACAO LEVA O MESMO TEMPO para ser executada. O trabalho e perfeitamente previsivel e balanceado." << std::endl;
    std::cout << "   - Vantagem: Possui o menor 'overhead' (custo de gerenciamento), pois a divisao do trabalho e feita apenas uma vez." << std::endl;
    std::cout << "   - Exemplo deste codigo: Este calculo e um caso PERFEITO para o 'static', pois a expressao a[i] = ... leva o mesmo tempo para qualquer valor de 'i'. Por isso, 'static' provavelmente sera mais rapido nos seus testes." << std::endl << std::endl;

    std::cout << "2. schedule(dynamic, chunk_size):" << std::endl;
    std::cout << "   - Como funciona: O OpenMP cria uma 'fila de trabalho' com blocos de 'chunk_size' iteracoes. Quando um thread fica livre, ele pega o proximo bloco disponivel na fila para executar." << std::endl;
    std::cout << "   - Quando usar: E ideal para loops onde o tempo de cada iteracao e VARIAVEL e IMPREVISIVEL. Por exemplo, se dentro do loop houvesse um 'if' que executasse um calculo muito mais pesado para certos valores de 'i'." << std::endl;
    std::cout << "   - Vantagem: Garante um excelente balanceamento de carga. Nenhum thread ficara ocioso se ainda houver trabalho a ser feito, pois os threads mais rapidos simplesmente pegam mais blocos da fila." << std::endl;
    std::cout << "   - Desvantagem: Possui um 'overhead' maior, pois os threads precisam constantemente se comunicar com a 'fila' para obter mais trabalho. Isso pode torna-lo mais lento em casos de trabalho uniforme." << std::endl;

    return 0;
}