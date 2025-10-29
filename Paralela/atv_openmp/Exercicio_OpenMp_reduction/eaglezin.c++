/*-------------------------------------------------------------------------------------------------------------------------
 * File Name : eaglezin.c++
 * Author    : Caio Silveira
 * Institution: IESB
 * Course    : Parallel and Distributed Programming
 * Objective : Demonstration of OpenMP reduction basics
 * Semester  : 2025/2
 --------------------------------------------------------------------------------------------------------------------------*/

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