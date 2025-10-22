/*-------------------------------------------------------------------------------------------------------------------------
 * File Name : eaglezin.c++
 * Author    : Caio Silveira
 * Institution: IESB
 * Course    : Parallel and Distributed Programming
 * Objective : Demonstration of OpenMP reduction basics
 * Semester  : 2025/2
 --------------------------------------------------------------------------------------------------------------------------*/


// ===============================================================
//                            ENUNCIADO
// ===============================================================



 /*

-----------------------------
1. Faça um programa que encontre o desvio padrão amostral.
de um conjunto de valores de  dois milhões de salários de uma
bigtech fictícia espalhadas nas americas. Escolha o nome da sua bigtech, 
assim como, dos departamentos e cargos.
-----------------------------

Utilizar de paralismo:

omp_lock
omp_reduction

 */



// ===============================================================
//                 PARTE DISCURSIVA DA RESOLUÇÃO
// ===============================================================


/*

Etapas lógicas:

1° - Nome da empresa? EagleZin, empresa para produção de teclados e periféricos;
2° - Quantidade de funcionários? 2.000.000
3° - Divisão desses funcionários em setores e unidades da bigtech?

Funcionários por país:

{
    Estados Unidos	78,000
    Canadá	55,000
    México	61,000
    Brasil	72,000
    Argentina	48,000
    Colômbia	50,000
    Chile	42,000
    Peru	39,000
    Venezuela	35,000
    Equador	33,000
    Bolívia	30,000
    Paraguai	27,000
    Uruguai	25,000
    Guiana	22,000
    Suriname	20,000
    Panamá	24,000
    Costa Rica	23,000
    Honduras	22,000
    Guatemala	21,000
    El Salvador	20,000
    Nicarágua	19,000
    Cuba	18,000
    República Dominicana	17,000
    Haiti	16,000
    Jamaica	15,000
    Trinidad e Tobago	14,000
    Barbados	13,000
    Bahamas	12,000
    Belize	11,000
    Granada	10,000
    Dominica	9,000
    Santa Lúcia	8,000
    São Vicente e Granadinas	7,000
    Antígua e Barbuda	6,000
    São Cristóvão e Neves	5,000
    }


Funcionários por Zona{
    América do Norte (EUA, Canadá, México): 194,000 funcionários

    América Central (20 países): 300,000 funcionários

    América do Sul (13 países): 1,506,000 funcionários
}

Retorno financeiro{
    $50.000 p/ano para cada 1 ano trabalhado pelo funcionário 
}

Cargos:
Montadores	
Engenheiros	
Design	    
Executivo	
Marketing	
Financeiro	

Salários por cargo:
Cargo	    Multiplicador sobre salário mínimo do continente:
Montadores	1.0×
Engenheiros	2.5×
Design	    2.0×
Executivo	3.0×
Marketing	1.8×
Financeiro	2.2×


4° - Fazer a média, variação e após desvio padrão [NESSA ORDEM];    

*/


// ===============================================================
//                 PARTE PRÁTICA DA RESOLUÇÃO
// ===============================================================

#include <cmath>
#include <omp.h>
#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <iomanip>

using namespace std;

struct Cargos {
    int montadores;
    int engenheiros;
    int design;
    int executivo;
    int marketing;
    int financeiro;

    int total() const {
        return montadores + engenheiros + design + executivo + marketing + financeiro;
    }
};

struct Pais {
    string nome;
    string grupoContinente; // Ex: "W" para América do Norte
    Cargos cargos;
};

int main() {
    // Salário mínimo por grupo de continente
    map<string, double> salarioMinimo = {
        {"W", 1500}, // América do Norte
        {"X", 900},  // América Central
        {"Y", 700}   // América do Sul
    };

    // Multiplicadores por cargo
    map<string, double> multiplicadorCargo = {
        {"montadores", 1.0},
        {"engenheiros", 2.5},
        {"design", 2.0},
        {"executivo", 3.0},
        {"marketing", 1.8},
        {"financeiro", 2.2}
    };

    // Lista de países
    vector<Pais> paises = {
        {"Estados Unidos", "W", {10000, 8000, 5000, 4000, 6000, 5000}},
        {"México", "W", {8000, 6000, 4000, 3000, 5000, 4000}},
        {"Panamá", "X", {3000, 2500, 1500, 1000, 2000, 1500}},
        {"Brasil", "Y", {12000, 10000, 6000, 5000, 8000, 7000}},
        {"Argentina", "Y", {7000, 6000, 4000, 3000, 5000, 4000}}
    };

    map<string, int> totalFuncionariosPorGrupo;
    map<string, double> totalGastoPorGrupo;
    map<string, double> totalRetornoPorGrupo;

    cout << fixed << setprecision(2);

    for (const auto& pais : paises) {
        double salarioBase = salarioMinimo[pais.grupoContinente];
        double gasto = 0.0;

        // Cálculo por cargo
        gasto += pais.cargos.montadores   * salarioBase * multiplicadorCargo["montadores"];
        gasto += pais.cargos.engenheiros  * salarioBase * multiplicadorCargo["engenheiros"];
        gasto += pais.cargos.design       * salarioBase * multiplicadorCargo["design"];
        gasto += pais.cargos.executivo    * salarioBase * multiplicadorCargo["executivo"];
        gasto += pais.cargos.marketing    * salarioBase * multiplicadorCargo["marketing"];
        gasto += pais.cargos.financeiro   * salarioBase * multiplicadorCargo["financeiro"];

        int totalFuncionarios = pais.cargos.total();
        double retorno = totalFuncionarios * 50000.0;

        cout << "País: " << pais.nome << endl;
        cout << "Grupo/Continente: " << pais.grupoContinente << endl;
        cout << "Total de funcionários: " << totalFuncionarios << endl;
        cout << "Gasto com salários (ajustado por cargo): $" << gasto << endl;
        cout << "Retorno financeiro: $" << retorno << endl;
        cout << "-----------------------------\n";

        totalFuncionariosPorGrupo[pais.grupoContinente] += totalFuncionarios;
        totalGastoPorGrupo[pais.grupoContinente] += gasto;
        totalRetornoPorGrupo[pais.grupoContinente] += retorno;
    }

    cout << "\nResumo por grupo/continente:\n";
    for (const auto& [grupo, total] : totalFuncionariosPorGrupo) {
        cout << "Grupo: " << grupo << endl;
        cout << "Total de funcionários: " << total << endl;
        cout << "Gasto total com salários: $" << totalGastoPorGrupo[grupo] << endl;
        cout << "Retorno total: $" << totalRetornoPorGrupo[grupo] << endl;
        cout << "-----------------------------\n";
    }

    return 0;
}
