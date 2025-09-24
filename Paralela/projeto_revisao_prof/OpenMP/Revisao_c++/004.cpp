/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 02/09/2025

*******************************************************************************/

#include <iostream>
#include <cmath>

using namespace std;

int main() {

    //
    // --- PARTE 3.a: Opearações entre dois números ---
    //

    int num1, num2;

    cout << "Digite o primeiro número inteiro: ";
    cin >> num1;

    cout << "Digite o segundo número inteiro: ";
    cin >> num2;

    cin.ignore();

    int soma = num1 + num2;

    //abs(num1-num2) para printar sempre um valor positivo, OBS: precisa da lib cmath inclusa
    int subtracao = abs(num1 - num2);
    int multiplicacao = num1 * num2;
    int divisaoInteira = num1 / num2;

    //Transformar int em um double para realizar a divisão
    double divisaoReal = static_cast<double>(num1) / num2;

    cout << "\nResultados das operações:" << endl;
    cout << "Soma: " << soma << endl;
    cout << "Subtração: " << subtracao << endl;
    cout << "Multiplicação: " << multiplicacao << endl;
    cout << "Divisão inteira: " << divisaoInteira << endl;
    cout << "Divisão real: " << divisaoReal << endl;

    //
    // --- PARTE 3.b: Qual o maior número? ---
    //

    // “Se num1 > num2, então maior recebe num1; caso contrário, recebe num2.”
    int maior = (num1 > num2) ? num1 : num2;

    //endl faz a quebra de linha e obriga que a linha seja impressa imediatamente

    cout << "\nO maior número é: " << maior << endl;

    return 0;
}
