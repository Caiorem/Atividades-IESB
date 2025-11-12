/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 14/10/2025

Questão 02:

Exercício 2 — Paralelizando um for simples
a) Crie um vetor v de tamanho 100 e inicialize todos os elementos com o valor 1.
b) Escreva um loop sequencial que soma todos os elementos.
c) Refaça o loop com #pragma omp parallel for reduction(+:soma).
d) Compare os resultados e explique por que a diretiva reduction é necessária.

*******************************************************************************/

#include <iostream>
#include <omp.h>
using namespace std;

int main(){

    int soma_sequencial, soma_paralela = 0;

    //a) Crie um vetor v de tamanho 100 e inicialize todos os elementos com o valor 1.
    int v[100];
    int i = 0;        
    while(i <= 100) { 
        v[i] = 1;
        i++;           
    }

    //b) Escreva um loop sequencial que soma todos os elementos.
    
    for(int i=0; i<100; i++){
        soma_sequencial += v[i];
    }
    std::cout << "A soma_sequencial eh: " << soma_sequencial<< std::endl;

    
    //c) Refaça o loop com #pragma omp parallel for reduction(+:soma).
    #pragma omp parallel for reduction(+:soma_paralela)
    for (int i=0; i<100; i++) {
        soma_paralela += v[i];
    }
    std::cout << "A soma_paralela eh: " << soma_paralela << std::endl;


    //d) Compare os resultados e explique por que a diretiva reduction é necessária.
    std::cout << "De acordo com a Microsoft 'Reduction' é Especifica que uma ou mais variáveis privadas para cada thread são objeto de uma operação de redução no final da região paralela." << std::endl;
    std::cout << "Ou seja: Ele ataca o laço for e divide o trabalho que seria só de um core.\n!!IMPORTANTE: Precisa ser for para funcionar" << std::endl;
    std::cout << "O resultados das duas somas é o mesmo, porém, a importância e motivação de utiliza-la é o ganho de performance" << std::endl;

    return 0;
}