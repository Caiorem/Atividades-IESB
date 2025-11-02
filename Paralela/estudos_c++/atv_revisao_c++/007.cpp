/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 09/09/2025

*******************************************************************************/

#include <iostream>
using namespace std;

    //
    // --- PARTE 6.a: função de soma  ---
    //

    void soma(int a, int b) {
    // OBS: Se você quiser usar o valor retornado é melhor jogar apenas o return a+b;
    cout << "Soma de dois números: " << (a + b) << endl;
    }

    //
    // --- PARTE 6.b: função incremento  ---
    //

    void incremento(int valor) {
    cout << "Incremento do primeiro número:" << (valor + 1) << endl;
    }

    //
    // --- PARTE 6.c: função de sobrecarga  ---
    //

    void soma(int a, int b, int c){
    cout << "Soma dos três números:" << (a+b+c) << endl;
    }

int main() {

    int num1, num2, num3;

    cout << "Digite o primeiro número inteiro: ";
    cin >> num1;

    cout << "Digite o segundo número inteiro: ";
    cin >> num2;

    cout << "Digite o segundo número inteiro: ";
    cin >> num3;
    
    cin.ignore();

    //Sobrecarga de funções: Chamar uma função com o mesmo nome, mas com parâmetros diferentes

    soma(num1, num2);
    incremento(num1);
    soma(num1, num2, num3);

    return 0;
}
