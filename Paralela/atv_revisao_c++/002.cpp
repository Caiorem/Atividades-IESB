/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 02/09/2025

*******************************************************************************/

#include <iostream>
#include <string>

using namespace std;

int main(){
    //
    // --- PARTE 1.a: Variáveis ---
    //

    // Declaração das variáveis para armazenar os dados do aluno
    string nome;
    int idade;
    double altura;
    bool aprovado;

    // Atribua valores a cada uma das variáveis
    // Exemplo:
    nome = "João da Silva";
    idade = 20;
    altura = 1.75;
    aprovado = true;

    cout << "Seu nome é " << nome << endl;
    cout << "Status: " << (aprovado ? "Aprovado":"Não")<< endl;

    //
    // --- PARTE 1.b: Constante e cálculo ---
    //

    // Declare uma constante para o valor de pi
    const double PI = 3.14159;

    // Declare a variável para o raio e atribua o valor 5
    double raio = 5.0;

    // Declare a variável para a área e calcule o valor usando a fórmula da área do círculo
    double area = PI * raio * raio;

    cout << "Área do círculo: "<< area << endl;

    return 0;
}