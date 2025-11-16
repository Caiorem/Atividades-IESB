💻 OpenMP: Mecanismos de Sincronização e Paralelismo em C++

Este repositório documenta uma série de exercícios práticos desenvolvidos para a disciplina de Programação Paralela e Distribuída (IESB 2025/2). O foco é na aplicação e demonstração das diferentes técnicas de sincronização e concorrência fornecidas pela API OpenMP.

🎯 Objetivos do Projeto

O projeto visa consolidar o entendimento sobre o gerenciamento de acesso a recursos compartilhados em um ambiente multithread, explorando como:

Garantir a precisão em operações de escrita.

Otimizar a execução de tarefas independentes (Embarrassingly Parallel).

Controlar o fluxo e a ordem de execução das threads.

🛠️ Mecanismos de Sincronização Explorados

Os exercícios utilizam uma base de dados de 2.000.000 de salários para ilustrar a aplicação e a necessidade dos seguintes mecanismos essenciais do OpenMP:

1. omp parallel for (Paralelismo de Dados)

É a diretiva fundamental para dividir um laço de repetição entre múltiplas threads, ideal para tarefas onde as iterações são totalmente independentes umas das outras.

Uso: Acelerar o processamento de grandes vetores de dados.

Exemplo: Cálculo do vetor de desvios (desvios[i] = todosSalarios[i] - media;).

2. omp CRITICAL

Define uma região crítica no código. Apenas uma thread pode entrar e executar este bloco por vez. Oferece proteção robusta para múltiplas operações complexas que manipulam dados compartilhados.

Uso: Proteger operações de escrita em variáveis compartilhadas complexas ou estruturas de dados (como std::map ou std::vector::push_back) quando a cláusula reduction não é uma opção viável.

3. omp ATOMIC

Garante que uma única operação de memória (geralmente uma atualização, como += ou *=) seja executada como uma operação indivisível. É a forma mais leve e eficiente de sincronização para estas atualizações simples, sendo geralmente mais rápida que CRITICAL.

Uso: Atualização de contadores ou somas simples, protegendo contra condições de corrida com o menor overhead possível.

4. omp BARRIER

Atua como um ponto de coordenação. Todas as threads ativas são forçadas a pausar ao atingir esta diretiva, esperando que todas as outras as alcancem. O fluxo de execução só prossegue quando todas as threads estão sincronizadas.

Uso: Garantir que uma etapa completa de cálculo (ex: cálculo da média) seja finalizada antes que a próxima etapa (ex: cálculo do desvio de cada ponto) comece.

5. omp LOCK (Funções de API)

O uso das funções da API (omp_lock_t, omp_init_lock, omp_set_lock, omp_unset_lock, omp_destroy_lock) oferece um controle de sincronização explícito e manual.

Uso: Demonstração de controle fino sobre o acesso a um recurso. É ideal quando a sincronização precisa ser gerenciada através de múltiplas funções ou requer lógica condicional complexa.

Exemplo: Proteção da variável somaSalarios no Passo 2 do código eaglezin_omp.cpp.

6. omp ORDERED

Força a execução de um bloco de código, aninhado dentro de um parallel for, a ocorrer na ordem das iterações do laço serial.

Uso: Essencial para garantir que as saídas (como impressões para o console) ou escritas de dados sequenciais sigam a ordem lógica, mesmo que o cálculo tenha sido feito em paralelo.

⚙️ Lembrete para compilação

Para compilar e linkar corretamente qualquer arquivo C++ que utilize OpenMP, é obrigatório incluir a flag -fopenmp:

Desenvolvido por Caio Silveira (IESB 2025/2)
