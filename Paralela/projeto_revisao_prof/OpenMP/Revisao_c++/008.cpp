/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 09/09/2025

*******************************************************************************/

#include <iostream>
#include <vector> //precisa incuir a lib para funcionar
using namespace std;


int main() {

    //
    // --- PARTE 7.a: valores em um array com a soma deles  ---
    //

    //Criação de um array

    int valores[5] = {3,4,2,1,6};
    int soma = 0;
    
    for (int i = 0; i <= 4; i++) {
        soma = soma + valores[i];
    }
    cout<<"Soma dos valores do array: "<<soma<<endl;

    //
    // --- PARTE 7.b: Vetor com com push_back ---
    //

    vector<int> valores_b = { 5, 10, 15};
    valores_b.push_back(20);
    valores_b.push_back(25);
    int soma_b = 0;

    for (int i = 0; i < valores_b.size(); i++) {
        soma_b += valores_b[i];  // soma_b = soma_b + numeros[i]
    }

    cout << "Soma valores do vetor: " << soma_b << endl;

    return 0;
}
