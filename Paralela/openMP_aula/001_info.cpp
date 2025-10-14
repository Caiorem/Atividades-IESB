#include <iostream>
#include <omp.h>

int main(){
    // num de processadores lógicos disponíveis  para o OpenMP
    int num_procs = omp_get_num_procs();

    //Num maximo de threads que o OPenMP usuaria por padrão
    int max_threads = omp_get_max_threads();

    std::cout << "Processadores logicos disponíveis: "<< num_procs << std::endl;
    std::cout << "Max de threads padrão (omp_get_max_threads): "<< num_procs << std::endl;

    //Para testes: Cada thread imprime seu ID
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int total = omp_get_num_threads();
        #pragma omp critical
        std::cout << "Sou a thread: "<< tid <<" de " << total << std::endl;
    }

    return 0;
}