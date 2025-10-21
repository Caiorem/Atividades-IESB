/*---------------------------------
Exercícios
---------------------------------*/

/*
 Utilize o código base abaixo para a resolução dos exercícios.
 Ao final de cada código, escreva um parágrafo com suas palavras

 a) Qual é o objetivo do código em detalhes.
 b) O que o seu código faz, etapa por etapa em detalhes.
 c) Ao final de cada exercício, ouvirei uma explicação sua sobre o que está sendo feito.
 
 */

 /*
  Explicações, datas:

  exercício 1 e 2 hoje: 07/10/2025.
  exercício 3 e 4 14/10/2025.
  exercício 5     21/10/2025.
 */

#include <iostream>
#include <vector>
#include <cmath>
#include <omp.h>

// Função para calcular as raízes de uma equação de segundo grau
// Retorna um std::pair contendo as raízes x1 e x2.
// Se não houver raízes reais, ambas serão 0.
std::pair<double, double> resolver_bhaskara(double a, double b, double c) {
    double delta = (b * b) - (4 * a * c);

    if (delta < 0) {
        return {0.0, 0.0};
    }

    double x1 = (-b + std::sqrt(delta)) / (2 * a);
    double x2 = (-b - std::sqrt(delta)) / (2 * a);

    return {x1, x2};
}

int main() {
    // Número de equações a serem resolvidas
    const int N = 1000;

    // Vetores para armazenar os coeficientes
    std::vector<double> a(N), b(N), c(N);

    // Preenche os vetores com valores de exemplo.
    // Metade terá raízes reais, a outra metade não.
    for (int i = 0; i < N; ++i) {
        a[i] = 1.0;
        if (i % 2 == 0) {
            // Equação com raízes reais: x^2 - 7x + 10 = 0 (raízes 5 e 2)
            b[i] = -7.0;
            c[i] = 10.0;
        } else {
            // Equação sem raízes reais: x^2 + 2x + 5 = 0 (delta < 0)
            b[i] = 2.0;
            c[i] = 5.0;
        }
    }

    // ===============================================================
    //               ÁREA PARA RESOLVER OS EXERCÍCIOS
    // ===============================================================

    std::pair <double, double> raizesTotais[N];
        
    /*--------------------------------------------
    funções lock    
    -------------------------------------------*/

    //variaveis que irao armazenar as somas pares e as somas impares
    double somaPares = 0.0;
    double somaImpares = 0.0;

    omp_lock_t lockPares;
    omp_lock_t lockImpares;

    #pragma omp parallel for
        //da inicio à regiao paralela do codigo. O loop for abaixo vai ser dividido entre 
        //todas as threads

        for (int i = 0; i < 16; ++i) {
            double somaRaizesLocais = 0.0;

            //cada thread calcula as raizes de suas variaveis
            std::pair<double, double> raizesLocais = resolver_bhaskara(a[i], b[i], c[i]);
            //realiza a soma das raizes de cada thread
            somaRaizesLocais = raizesLocais.first + raizesLocais.second;
            
            if (i % 2 == 0){
                //caso o indice seja par, utilizar-se do lockPares. Ele ira garantir que apenas essa thread
                //acesse essa porcao de codigo. Enquanto isso, outras threads esperam aqui para poderem receber
                //essa lock.

                omp_set_lock(&lockPares);
                somaPares += somaRaizesLocais; 

                //Apos acessar a variavel somaPares, deve-se liberar a lock para que outras threads possam uza-la
                omp_unset_lock(&lockPares);
            
            }else{
                //em caso else, fazer o que foi feito anteriormente so que com lockImpar

                omp_set_lock(&lockImpares);
                somaImpares += somaRaizesLocais;

                omp_unset_lock(&lockImpares);

            }

        }
        //deve-se destruir as locks apos o uso para liberar a memoria do sistema
        omp_destroy_lock(&lockPares);
        omp_destroy_lock(&lockImpares);

        std::cout << "Somas pares das raizes: " << somaPares << "\n";
        std::cout << "Somas ímpares das raizes: " << somaImpares << "\n";
        std::cout << "Soma total: " << somaPares + somaImpares << "\n";

    // ===============================================================

    return 0;
}
