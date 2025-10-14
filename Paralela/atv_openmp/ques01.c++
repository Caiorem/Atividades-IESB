/******************************************************************************

Caio Silveira - 2312130166
Last Edit - 14/10/2025

Questão 01:

Exercício 1 — “Hello World” Paralelo
a) Crie uma região paralela com #pragma omp parallel.
b) Cada thread deve imprimir uma mensagem indicando seu número (omp_get_thread_num()) e o total de threads (omp_get_num_threads()).
c) Configure o programa para rodar com 4 threads.

*******************************************************************************/

#include <iostream>
#include <omp.h>
using namespace std;

int main(){

    //c) Configure o programa para rodar com 4 threads.
    omp_set_num_threads(4);

    /// a) Crie uma região paralela com #pragma omp parallel.
    #pragma omp parallel

    //TUDO DENTRO DESSE BLOCO SERÁ PARALELIZADO
    {
 
    //b) Cada thread deve imprimir uma mensagem indicando seu número (omp_get_thread_num()) e o total de threads (omp_get_num_threads()).
        int threadID = omp_get_thread_num();
        cout<<threadID<<". Yellow Submarine!"<<endl;
    }
    return 0;
}