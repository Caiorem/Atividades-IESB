/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 09/09/2025

*******************************************************************************/

#include <iostream>
using namespace std;


int main() {

    //
    // --- PARTE 8.a: Ponteiro inicial ---
    //

    int x = 10;
    int original = x;
    cout << "Valor inicial variável x: "<<x<<endl;
 
    int* ptr = &x;
    *ptr = *ptr * 2;
    cout << "Valor duplicado em ponteiro a variável x: "<<*ptr<<endl;

    //Valor por referência = É tipo um alias, é um outro nome da variável, só pode existir
    //logicamente se a variável já existir
    //OBS: Modifica o valor inicial da variável, muda o valor que está no endereço

    int& ref = x;
    ref = original * 3;
    cout << "Valor triplicado em referência a variável x: "<<ref<<endl;

    //
    // --- PARTE 8.b: Ponteiro dinâmico e liberar memória ---
    //

    int* p = new int;  // cria espaço na memória para um int
    *p = 42;           // coloca um valor nesse espaço
    cout << "Valor do ponteiro: "<<*p<<endl;

    delete p;  // libera o espaço alocado, em projetos pequenos passa batido, mas em
    //grandes aplicações se faz importante, quando fica "vazio" um ponteiro o espaço de
    //memória se mantém ativo, o que pode comprometer um futuro da aplicação maior;
    p = nullptr; // opcional, evita ponteiro "pendurado, com necas de pitibiricas"
    cout << "Valor do ponteiro: "<<*p<<endl;

    return 0;
}
