/*-------------------------------------------------------------------------------------------------------------------------
 * File Name : eaglezin_omp.cpp
 * Author    : Caio Silveira (Adaptado e Paralelizado por Gemini)
 * Institution: IESB
 * Course    : Parallel and Distributed Programming
 * Objective : Demonstration of OpenMP reduction for Standard Deviation calculation
 * Semester  : 2025/2
 --------------------------------------------------------------------------------------------------------------------------*/

// ===============================================================
// 			  PARTE PRÁTICA DA RESOLUÇÃO
// ===============================================================

// INCLUSÃO DE BIBLIOTECAS NECESSÁRIAS
#include <cmath> 		// Biblioteca matemática (cálculos numéricos)
#include <omp.h> 		// **OpenMP Library for Parallelism**
#include <iostream> 	// Input/Output para exibição de dados no console
#include <vector> 		// Container dinâmico para armazenar sequências
#include <map> 			// Estrutura de dados key-value para mapeamentos
#include <string> 		// Manipulação de strings
#include <iomanip> 		// Manipulação de formato de entrada/saída (precisão decimal)
#include <numeric>      // Usado para garantir a lógica de redução em mapas
#include <algorithm>    // Algoritmos gerais

using namespace std; 	// Usando namespace padrão para evitar prefixo "std::"

// ===============================================================
// 		  	 DEFINIÇÃO DE ESTRUTURAS DE DADOS
// ===============================================================

// ESTRUTURA: Cargos
// Objetivo: Armazenar a quantidade de funcionários em cada cargo dentro de um país
struct Cargos {
    int montadores; 	// Quantidade de operários/montadores
    int engenheiros; 	// Quantidade de engenheiros
    int design; 		// Quantidade de profissionais de design/UX
    int executivo; 		// Quantidade de executivos/gestores
    int marketing; 		// Quantidade de profissionais de marketing
    int financeiro; 	// Quantidade de profissionais de financeiro

    // MÉTODO: total()
    // Descrição: Retorna a soma total de todos os funcionários em todos os cargos
    // Retorno: Inteiro com o total de funcionários
    int total() const {
        return montadores + engenheiros + design + executivo + marketing + financeiro;
    }
};

// ESTRUTURA: Pais
// Objetivo: Armazenar informações sobre um país (nome, localização, distribuição de cargos)
struct Pais {
    string nome; 	    	// Nome do país (ex: "Brasil")
    string grupoContinente; // Grupo de continente (ANorte, ACentral, ASul)
    Cargos cargos; 			// Distribuição de cargos neste país
};

int main() {
    // Definindo o número de threads (opcional, apenas para demonstração)
    omp_set_num_threads(8);

    // ===============================================================
    // 		   ETAPA 1: INICIALIZAÇÃO DE DADOS E ESTRUTURAS
    // ===============================================================

    // MAP 1: Salário mínimo por grupo de continente
    map<string, double> salarioMinimo = {
        {"ANorte", 1500.0}, // América do Norte - salário base mais alto
        {"ACentral", 900.0},  // América Central - salário intermediário
        {"ASul", 700.0}   // América do Sul - salário base mais baixo
    };

    // MAP 2: Multiplicadores por cargo
    map<string, double> multiplicadorCargo = {
        {"montadores", 1.0}, 	// Sem multiplicação - salário base
        {"engenheiros", 2.5}, 	// 2.5x o salário base
        {"design", 2.0}, 		// 2.0x o salário base
        {"executivo", 3.0}, 	// 3.0x o salário base (maior multiplicador)
        {"marketing", 1.8}, 	// 1.8x o salário base
        {"financeiro", 2.2} 	// 2.2x o salário base
    };

    // VECTOR: Lista de países com informações completas (Total de 2.000.000 de funcionários)
    // Multiplicador base (x12) + ajuste para 2.000.000 exatos.
    vector<Pais> paises = {
        // Total: 578,000 (122,000 de ajuste somado aqui)
        {"Estados Unidos", "ANorte", {242000, 96000, 60000, 48000, 72000, 60000}}, 	
        // Total: 360,000
        {"Mexico", "ANorte", {96000, 72000, 48000, 36000, 60000, 48000}}, 	 	
        // Total: 138,000
        {"Panamá", "ACentral", {36000, 30000, 18000, 12000, 24000, 18000}}, 		 	
        // Total: 576,000
        {"Brasil", "ASul", {144000, 120000, 72000, 60000, 96000, 84000}}, 		
        // Total: 348,000
        {"Argentina", "ASul", {84000, 72000, 48000, 36000, 60000, 48000}} 		
    };

    // ===============================================================
    // 		   ETAPA 2: DECLARAÇÃO DE VARIÁVEIS ACUMULADORAS
    // ===============================================================
    
    map<string, int> totalFuncionariosPorGrupo;
    map<string, double> totalGastoPorGrupo;
    map<string, double> totalRetornoPorGrupo;

    // ===============================================================
    // 		   ETAPA 3: CONFIGURAÇÃO DE FORMATO DE SAÍDA
    // ===============================================================
    cout << fixed << setprecision(2);

    // ===============================================================
    // 		   ETAPA 4: LOOP PRINCIPAL - PROCESSAMENTO POR PAÍS (SERIAL)
    // ===============================================================
    
    // Processamento de agregação por grupo de continente (Mapas)
    // é mantido como serial para evitar condições de corrida na modificação da estrutura do mapa.
    
    for (const auto& pais : paises) {
        // SUB-ETAPA 4.1: Recuperação do salário base para o grupo do país
        double salarioBase = salarioMinimo[pais.grupoContinente];

        // SUB-ETAPA 4.2: Inicialização da variável acumuladora de gasto
        double gasto = 0.0; 	

        // SUB-ETAPA 4.3: CÁLCULO DE GASTO POR CARGO (REDUCTION IMPLÍCITA)
        gasto += pais.cargos.montadores 	* salarioBase * multiplicadorCargo["montadores"];
        gasto += pais.cargos.engenheiros 	* salarioBase * multiplicadorCargo["engenheiros"];
        gasto += pais.cargos.design 		* salarioBase * multiplicadorCargo["design"];
        gasto += pais.cargos.executivo 		* salarioBase * multiplicadorCargo["executivo"];
        gasto += pais.cargos.marketing 		* salarioBase * multiplicadorCargo["marketing"];
        gasto += pais.cargos.financeiro 	* salarioBase * multiplicadorCargo["financeiro"];

        // SUB-ETAPA 4.4: CÁLCULO DE MÉTRICAS TOTAIS DO PAÍS
        int totalFuncionarios = pais.cargos.total();
        double retorno = totalFuncionarios * 50000.0; // $50.000 de retorno por funcionário

        // SUB-ETAPA 4.6: ACUMULAÇÃO EM MAPAS GLOBAIS (SERIAL - por segurança de Mapas)
        totalFuncionariosPorGrupo[pais.grupoContinente] += totalFuncionarios;
        totalGastoPorGrupo[pais.grupoContinente] += gasto;
        totalRetornoPorGrupo[pais.grupoContinente] += retorno;
    }

    // ===============================================================
    // 	  ETAPA 6: CÁLCULO DO DESVIO PADRÃO AMOSTRAL DOS SALÁRIOS
    // ===============================================================
    
    cout << "\n\n═════════════════════════════════════════════════════════════\n";
    cout << "CÁLCULO DO DESVIO PADRÃO AMOSTRAL DOS SALÁRIOS (PARALELIZADO)\n";
    cout << "Threads ativas: " << omp_get_max_threads() << "\n";
    cout << "═════════════════════════════════════════════════════════════\n";

    // ─────────────────────────────────────────────────────────────
    // PASSO 1: GERAR VETOR COM TODOS OS SALÁRIOS (SERIAL)
    // ─────────────────────────────────────────────────────────────
    
    vector<double> todosSalarios; 	
    
    cout << "\n[PASSO 1] Gerando vetor de todos os salários...\n";
    
    for (const auto& pais : paises) {
        double salarioBase = salarioMinimo[pais.grupoContinente];
        
        // Loop para preencher o vetor. Mantido serial devido à complexidade 
        // de paralelizar 'push_back' com OpenMP sem 'critical' ou pré-alocação.
        auto add_salaries = [&](const string& cargo, int count) {
            double salario = salarioBase * multiplicadorCargo.at(cargo);
            for (int i = 0; i < count; i++) {
                todosSalarios.push_back(salario);
            }
        };

        add_salaries("montadores", pais.cargos.montadores);
        add_salaries("engenheiros", pais.cargos.engenheiros);
        add_salaries("design", pais.cargos.design);
        add_salaries("executivo", pais.cargos.executivo);
        add_salaries("marketing", pais.cargos.marketing);
        add_salaries("financeiro", pais.cargos.financeiro);
    }
    
    int totalSalarios = todosSalarios.size();
    // Confirmação do tamanho do vetor
    cout << "✓ Total de salários gerados: " << totalSalarios << " (2.000.000 esperados)" << endl; 

    // ─────────────────────────────────────────────────────────────
    // PASSO 2: CALCULAR A SOMA DOS SALÁRIOS USANDO OMP LOCK
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n[PASSO 2] Calculando a soma dos salários (Usando omp lock)\n";
    
    double somaSalarios = 0.0;
    
    // DECLARAÇÃO E INICIALIZAÇÃO DO OMP LOCK
    omp_lock_t soma_lock;
    omp_init_lock(&soma_lock);
    
    // ⚠️ USO DE OMP LOCK PARA DEMONSTRAÇÃO (REDUCTION é o método preferido)
    // #pragma omp parallel for
    #pragma omp parallel for
    for (int i = 0; i < totalSalarios; i++) {
        // Bloqueia o acesso à variável compartilhada 'somaSalarios'
        omp_set_lock(&soma_lock); 
        somaSalarios += todosSalarios[i];
        // Libera o acesso
        omp_unset_lock(&soma_lock);
    }
    
    // DESTRUIÇÃO DO OMP LOCK
    omp_destroy_lock(&soma_lock);
    
    double media = somaSalarios / totalSalarios;
    cout << "✓ Soma total de salários: $" << somaSalarios << endl;
    cout << "✓ Média de salários: $" << media << endl;

    // ─────────────────────────────────────────────────────────────
    // PASSO 3: CALCULAR DESVIO DE CADA PONTO (EMBARRASSINGLY PARALLEL)
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n[PASSO 3] Calculando desvios individuais de cada salário...\n";
    
    vector<double> desvios(totalSalarios);
    
    // ⚠️ OPORTUNIDADE DE PARALELISMO #3: IMPLEMENTADA SEM DEPENDÊNCIA
    // #pragma omp parallel for
    #pragma omp parallel for
    for (int i = 0; i < totalSalarios; i++) {
        desvios[i] = todosSalarios[i] - media;
    }
    cout << "✓ Desvios calculados para todos os " << totalSalarios << " salários\n";

    // ─────────────────────────────────────────────────────────────
    // PASSO 4: ELEVAR DESVIOS AO QUADRADO E SOMAR (USANDO REDUCTION)
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n[PASSO 4] Elevando desvios ao quadrado e somando (Usando Reduction)...\n";
    
    double somaDesviosAoQuadrado = 0.0;
    
    // ⚠️ OPORTUNIDADE DE PARALELISMO #4: USANDO REDUCTION (Método mais eficiente)
    // #pragma omp parallel for reduction(+:somaDesviosAoQuadrado)
    #pragma omp parallel for reduction(+:somaDesviosAoQuadrado)
    for (int i = 0; i < totalSalarios; i++) {
        somaDesviosAoQuadrado += desvios[i] * desvios[i];
    }
    cout << "✓ Soma dos desvios ao quadrado: " << somaDesviosAoQuadrado << endl;

    // ─────────────────────────────────────────────────────────────
    // PASSO 5: CALCULAR VARIÂNCIA AMOSTRAL
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n[PASSO 5] Calculando variância amostral...\n";
    
    // Usa (n-1) porque é variância AMOSTRAL
    double varianciaAmostral = somaDesviosAoQuadrado / (totalSalarios - 1);
    cout << "✓ Variância amostral: " << varianciaAmostral << endl;

    // ─────────────────────────────────────────────────────────────
    // PASSO 6: CALCULAR DESVIO PADRÃO AMOSTRAL
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n[PASSO 6] Calculando desvio padrão amostral (resultado final)...\n";
    
    double desvioPadraoAmostral = sqrt(varianciaAmostral);
    
    cout << "═════════════════════════════════════════════════════════════\n";
    cout << "✓ DESVIO PADRÃO AMOSTRAL DOS SALÁRIOS: $" << desvioPadraoAmostral << endl;
    cout << "═════════════════════════════════════════════════════════════\n";

    // ─────────────────────────────────────────────────────────────
    // RESUMO ESTATÍSTICO
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n📊 RESUMO ESTATÍSTICO DOS SALÁRIOS:\n";
    cout << "────────────────────────────────────────────────────────────\n";
    cout << "Total de funcionários: " << totalSalarios << endl;
    cout << "Soma total de salários: $" << somaSalarios << endl;
    
    double totalRetornoGlobal = std::accumulate(totalRetornoPorGrupo.begin(), totalRetornoPorGrupo.end(), 0.0,
                                                [](double sum, const auto& pair) { return sum + pair.second; });
    cout << "Soma total de retorno financeiro: $" << totalRetornoGlobal << endl;
    cout << "Média de salários: $" << media << endl;
    cout << "Variância amostral: " << varianciaAmostral << endl;
    cout << "Desvio padrão amostral: $" << desvioPadraoAmostral << endl;
    cout << "────────────────────────────────────────────────────────────\n";
    
    // ─────────────────────────────────────────────────────────────
    // INTERPRETAÇÃO
    // ─────────────────────────────────────────────────────────────
    
    cout << "\n📌 INTERPRETAÇÃO:\n";
    cout << "O desvio padrão de $" << desvioPadraoAmostral << " significa que, em média,\n";
    cout << "os salários se desviam $" << desvioPadraoAmostral << " da média ($" << media << ").\n";
    cout << "Quanto MENOR o desvio padrão, mais UNIFORMES são os salários.\n";
    cout << "Quanto MAIOR o desvio padrão, mais VARIADOS são os salários.\n";
    
    // Impressão final solicitada pelo usuário
    cout << "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    cout << "TOTAL FINAL DE FUNCIONÁRIOS (SALÁRIOS PROCESSADOS): " << totalSalarios << endl;
    cout << "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";


    return 0; 	// Retorna 0 indicando sucesso na execução
}