#include <iostream>
#include <omp.h>
using namespace std;

int main(){

    //criar um conjunto de "n" threads
    //por default, a mesma quantidade de cores(núcleos) lógicos no computador
    #pragma omp parallel

    //TUDO DENTRO DESSE BLOCO SERÁ PARALELIZADO
    {
        int threadID = omp_get_thread_num();
        cout<<threadID<<". Yellow Submarine!"<<endl;
    }

    //Obs: como todas as threads são paralelas na hora de printar, o print pode 
    //sair fora de ordem

    return 0;
}