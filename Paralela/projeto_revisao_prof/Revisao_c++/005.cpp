/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 02/09/2025

*******************************************************************************/

#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main()
{

    //
    // --- PARTE 4.a: Relação de aprovação, usando um elemento lógico ---
    //

    double nota;
    cout << "Digite sua nota (0 a 10): ";
    cin >> nota;

    if(nota >= 6){
        cout << "Aprovado" << endl;
    } else if(4 <= nota && nota <= 6){
        cout << "Prova final" << endl;
    } else {
        cout << "Reprovado" << endl;
    }

    //
    // --- PARTE 4.b: Criação de vetor e uso de laços de repetição ---
    //
    
    //Criação de um vetor em c++:
    vector<string> nomes;
    int opcao;

    do {
        cout << "\nMenu:" << endl;
        cout << "1 - Cadastrar nome" << endl;
        cout << "2 - Listar nomes" << endl;
        cout << "3 - Sair" << endl;
        cout << "Escolha uma opção: ";
        cin >> opcao;

        cin.ignore();

        switch (opcao) {
            case 1: {
                string nome;
                cout << "Digite o nome: ";
                getline(cin, nome);

                //Push_back é um metódo do Vetor para adicionar um elemento no final do
                //vetor
                nomes.push_back(nome);
                cout << "Nome cadastrado com sucesso!" << endl;
                break;
            }
            case 2: {
                cout << "\nLista de nomes cadastrados:" << endl;
                if (nomes.empty()) {
                    cout << "Nenhum nome cadastrado ainda." << endl;
                } else {
                    for (size_t i = 0; i < nomes.size(); ++i) {
                        cout << i + 1 << ". " << nomes[i] << endl;
                    }
                }
                break;
            }
            case 3:
                cout << "Encerrando o programa..." << endl;
                break;
            default:
                cout << "Opção inválida. Tente novamente." << endl;
        }

    } while (opcao != 3);

    return 0;
}