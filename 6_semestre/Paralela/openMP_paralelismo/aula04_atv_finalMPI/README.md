## 📌 Sobre o Projeto

Este projeto contém um programa em **MPI (Message Passing Interface)** que divide um vetor entre vários processos, distribui o trabalho e coleta as somas parciais enviadas pelos processos trabalhadores.

O programa utiliza o modelo de **paralelismo distribuído**, no qual cada processo tem sua própria memória e precisa trocar mensagens para cooperar.

---

# 🧪 Como Compilar e Executar

## ✔ Pré-requisitos

Instale MPI no Linux:

```bash
sudo apt install mpich
```

ou

```bash
sudo apt install openmpi-bin libopenmpi-dev
```

Verifique:

```bash
mpic++ --version
mpirun --version
```

---

## ✔ Compilar o código

Supondo que o arquivo se chame `trabalho.cpp`:

```bash
mpic++ trabalho.cpp -o trabalho
```

Isso criará um executável chamado **trabalho**.

---

## ✔ Executar o programa

Execute com pelo menos **2 processos** (1 mestre + 1 trabalhador):

```bash
mpirun -np 4 ./trabalho
```

Exemplo com 4 processos:

* Processo 0 = Mestre
* Processos 1, 2, 3 = Trabalhadores

---

# 🧠 Diferença entre MPI e OpenMP

O projeto usa **MPI**, mas é importante entender como ele se diferencia do **OpenMP**, outro modelo popular de paralelismo.

---

# 🟧 MPI (OpenMPI / MPICH)

### ✔ Modelo: **Memória distribuída**

Cada processo tem sua **própria memória**, e a comunicação é feita através de **mensagens**:

* `MPI_Send`
* `MPI_Recv`
* `MPI_Bcast`, etc.

### ✔ Uso típico:

* Clusters e supercomputadores
* Computadores conectados em rede
* Sistemas com múltiplas máquinas físicas

### ✔ Características:

* Escala muito bem (centenas ou milhares de nós)
* Comunicação explícita
* Programação mais complexa

---

# 🟦 OpenMP

### ✔ Modelo: **Memória compartilhada**

Todos os threads compartilham a **mesma memória RAM**.

Exemplo:

```cpp
#pragma omp parallel for
for (int i = 0; i < N; i++)
    a[i] = b[i] + c[i];
```

### ✔ Uso típico:

* Uma única máquina com vários núcleos
* Paralelizar loops e seções de código

### ✔ Características:

* Fácil de usar
* Não funciona entre máquinas diferentes
* Não envolve envio de mensagens

---

# 📌 Resumo

* **OpenMP** → para paralelizar em *uma única máquina*.
* **MPI** → para paralelizar em *várias máquinas ou processos independentes*.
* Este projeto usa **MPI** porque cada processo executa isolado e troca mensagens com o mestre.

---

# ✔ Quer que eu adicione um diagrama ou imagem explicando o fluxo mestre/trabalhadores?

Posso incluir também exemplos de saída, instruções para clusters SLURM, ou uma seção “Como funciona o código internamente”.
