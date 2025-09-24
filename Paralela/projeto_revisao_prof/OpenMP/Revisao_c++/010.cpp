/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 09/09/2025

*******************************************************************************/

#include <iostream>
#include <string>
#include <vector>
using namespace std;


struct Aluno{
    string nome_completo;
    int idade;
};

class ContaBancaria {
//Por que usar private? Para proteger o saldo de acessos diretos e garantir que ele só possa ser modificado através dos métodos da classe.
private:
    double saldo;  // saldo da conta

public:
    // Construtor para inicializar o saldo
    ContaBancaria() {
        saldo = 0;
    }

    vector<string> extrato; // vetor para armazenar o extrato

    
    // Método para depositar dinheiro
    void depositar(double valor) {
        if (valor > 0) {
            saldo += valor;
            cout << "Depositado: " << valor << endl;
            extrato.push_back(string("\033[1;32m") + "Depósito: +" + to_string(valor) + "\033[0m");
        //to_string converte o valor double para string, pode ser usado em outros tipos também
        //ex: to_string(int), to_string(float), to_string(char)...
        } else {
            cout <<"Depósito de "<<valor<<" reais é inválido!" << endl;
        }
    }

    // Método para sacar dinheiro
    void sacar(double valor) {
        if (valor <= saldo && valor > 0) {
            saldo -= valor;
            cout << "Sacado: " << valor << endl;
        extrato.push_back(string("\033[1;31m") + "Saque: -" + to_string(valor) + "\033[0m");
        } else {
            cout << "Não é possível sacar "<<valor<<" reais. Saldo insuficiente ou valor inválido!" << endl;
        }
    }

    // Método para imprimir o saldo atual
    void imprimir() {
        cout << "-------------------------"<<endl;
        cout << "   Banco do Estudante    "<< endl;
        cout << "Saldo atual: " << saldo << endl;
        cout << "-------------------------"<<endl;
        cout << "EXTRATO:" << endl;
        for (const auto& transacao : extrato) {
            cout << transacao << endl;
        }
         cout << "-------------------------"<<endl;
    }
};


int main() {

    //
    // --- PARTE 9.a: Criar um struct e preencher ele com dados do aluno---
    //

    Aluno a1;
    cout<< "Digite seu nome completo: ";
    getline(cin, a1.nome_completo);

    cout<< "Digite sua idade: ";
    cin >> (a1.idade);

    cout << "-------------------------"<<endl;
    cout << "Nome do aluno: "<<a1.nome_completo<<endl;
    cout << "Idade do aluno: "<<a1.idade<<" anos"<<endl;
    cout << "-------------------------"<<endl;


    //
    // --- PARTE 9.b: Criar mini sistema bancário---
    //


    ContaBancaria minhaConta;

    minhaConta.depositar(100.0);
    minhaConta.sacar(30.0);
    minhaConta.imprimir();

    minhaConta.sacar(100.0);  // Teste saque maior que o saldo
    minhaConta.depositar(-10.0); // Teste depósito inválido

    minhaConta.imprimir();

    return 0;
}
