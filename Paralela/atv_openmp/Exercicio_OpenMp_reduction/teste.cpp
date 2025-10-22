#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <iomanip>

using namespace std;

struct CargoDistribuicao {
    int montadores;
    int engenheiros;
    int design;
    int executivo;
    int marketing;
    int financeiro;
};

struct Pais {
    string nome;
    string continente;
    int funcionarios;
    CargoDistribuicao cargos;
    double salarioMedio; // em USD
};

double calcularGastoSalarial(const Pais& pais) {
    return pais.funcionarios * pais.salarioMedio;
}

double calcularRetornoFinanceiro(const Pais& pais) {
    return pais.funcionarios * 50000.0;
}

int main() {
    vector<Pais> paises = {
        {"Brasil", "América do Sul", 72000, {15000, 12000, 8000, 6000, 18000, 13000}, 650},
        {"Estados Unidos", "América do Norte", 78000, {16000, 14000, 9000, 7000, 20000, 12000}, 5014},
        {"México", "América do Norte", 61000, {13000, 10000, 7000, 5000, 16000, 10000}, 1100},
        {"Argentina", "América do Sul", 48000, {10000, 8000, 6000, 4000, 12000, 8000}, 1800},
        {"Panamá", "América Central", 24000, {5000, 4000, 3000, 2000, 6000, 4000}, 1288}
        // Adicione mais países conforme necessário
    };

    map<string, int> totalPorContinente;
    map<string, double> gastoPorContinente;
    map<string, double> retornoPorContinente;

    cout << fixed << setprecision(2);
    for (const auto& pais : paises) {
        double gasto = calcularGastoSalarial(pais);
        double retorno = calcularRetornoFinanceiro(pais);

        cout << "País: " << pais.nome << endl;
        cout << "Continente: " << pais.continente << endl;
        cout << "Funcionários: " << pais.funcionarios << endl;
        cout << "Salário médio: $" << pais.salarioMedio << endl;
        cout << "Gasto salarial: $" << gasto << endl;
        cout << "Retorno financeiro: $" << retorno << endl;
        cout << "Cargos:\n";
        cout << "  Montadores: " << pais.cargos.montadores << endl;
        cout << "  Engenheiros: " << pais.cargos.engenheiros << endl;
        cout << "  Design: " << pais.cargos.design << endl;
        cout << "  Executivo: " << pais.cargos.executivo << endl;
        cout << "  Marketing: " << pais.cargos.marketing << endl;
        cout << "  Financeiro: " << pais.cargos.financeiro << endl;
        cout << "-----------------------------\n";

        totalPorContinente[pais.continente] += pais.funcionarios;
        gastoPorContinente[pais.continente] += gasto;
        retornoPorContinente[pais.continente] += retorno;
    }

    cout << "\nResumo por continente:\n";
    for (const auto& [continente, total] : totalPorContinente) {
        cout << "Continente: " << continente << endl;
        cout << "Total de funcionários: " << total << endl;
        cout << "Gasto salarial: $" << gastoPorContinente[continente] << endl;
        cout << "Retorno financeiro: $" << retornoPorContinente[continente] << endl;
        cout << "-----------------------------\n";
    }

    return 0;
}
