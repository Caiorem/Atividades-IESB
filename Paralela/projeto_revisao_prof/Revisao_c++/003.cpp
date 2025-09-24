/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 02/09/2025

*******************************************************************************/

#include <iostream>
#include <string>

// Como isso foi escrito no começo, não seria necessário colocar o std::cout em cada 
// linha nova de impressão
using namespace std;
// OBS: Em projetos maiores não é interessante declarar globalmente o std


int main()
{

    //
    // --- PARTE 1.a: Entrada Saída ---
    //

    string Nome;
    cout << "Qual seu nome? ";
    
    //Definir variável de entrada para a variável
    cin >> Nome;
    

    int age;
    cout << "Quantos anos você tem? ";
    cin >> age;

    cout << "Olá, " << Nome << "! Você tem " << age << " anos." << endl;

    // Limpar os /n que restaram no buffer que restaram dos cin anteriores
    cin.ignore();

    //
    // --- PARTE 2.b: Nome completo ---
    //

    string fullName;
    cout << "Escreva seu nome completo: ";

    //Utiliza-se getline para ler toda linha, até mesmo os espaços, Ex "Caio Silveira 
    // Guimarães" se fosse apenas cin ele leria "Caio" apenas.
    getline(cin, fullName);

    cout << "Seu nome completo é: " << fullName << endl;

    return 0;
}