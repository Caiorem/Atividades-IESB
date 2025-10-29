/*-------------------------------------------------------------------------------------------------------------------------
 * File Name : eaglezin.c++
 * Author    : Caio Silveira
 * Institution: IESB
 * Course    : Parallel and Distributed Programming
 * Objective : Demonstration of OpenMP reduction basics
 * Semester  : 2025/2
 --------------------------------------------------------------------------------------------------------------------------*/


// ===============================================================
//                            ENUNCIADO
// ===============================================================


-----------------------------
1. Faça um programa que encontre o desvio padrão amostral.
de um conjunto de valores de  dois milhões de salários de uma
bigtech fictícia espalhadas nas americas. Escolha o nome da sua bigtech, 
assim como, dos departamentos e cargos.
-----------------------------

Utilizar de paralismo:

omp_lock
omp_reduction


// ===============================================================
//                 PARTE DISCURSIVA DA RESOLUÇÃO
// ===============================================================


Etapas lógicas:

1° - Nome da empresa? EagleZin, empresa para produção de teclados e periféricos;
2° - Quantidade de funcionários? 2.000.000
3° - Divisão desses funcionários em setores e unidades da bigtech?

Funcionários por país:

{
    5 países (2 América do Norte, 1 América Central, 2 América do Sul)

    País:           Percentual  Funcionários por país
    Brasil	        30,67%	    613.418
    Estados Unidos	24,28%	    485.623
    México	        19,17%	    383.387
    Argentina	    18,53%	    370.607
    Panamá	        7,35%	    146.965
}

Funcionários por Zona{
    América do Norte (EUA e México): 869.010 funcionários

    América Central (Panamá): 146.695 funcionários

    América do Sul (Brasil e Argentina): 985.025 funcionários
}

Retorno financeiro{
    No mínimo $50.000 p/ano para cada 1 ano trabalhado pelo funcionário 
}

Cargos{
    Montadores	
    Engenheiros	
    Design	    
    Executivo	
    Marketing	
    Financeiro
}	

Salários por cargo:
    Cargo	    Multiplicador sobre salário mínimo do continente:
    Montadores	1.0×
    Engenheiros	2.5×
    Design	    2.0×
    Executivo	3.0×
    Marketing	1.8×
    Financeiro	2.2×


4° - Fazer a média, variação e após desvio padrão [NESSA ORDEM];    
    4.1° - Calcula a media
    4.2° - Calcular desvio cada ponto
    4.3° - Elevar desvio de cada ponto ao quadrado
    4.4° - Calcular variancia (Soma de desvios divido pelo total de passos)
    4.5° - Desvio padrão (Raiz do valor encontrado no passo anterior)

5° - Fazer relação de custos e ganhos
    5.1° - Fazer quantidade de custo por cada filial
    5.2° - Fazer relação de ganhos por filial


