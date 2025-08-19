# grafo_matriz.py

from grafo_interface import Grafo

class GrafoMatrizAdjacencia(Grafo):
    """
    Implementação de um grafo não ordenado usando uma Matriz de Adjacência.
    """
    def __init__(self, num_vertices, mapeamento_letras):
        self.num_vertices = num_vertices
        self.adj_matrix = [[0] * num_vertices for _ in range(num_vertices)]
        self.mapeamento_letras = mapeamento_letras
        self.mapeamento_indices = {letra: i for i, letra in enumerate(mapeamento_letras)}
        self.mapeamento_letras_por_indice = {i: letra for letra, i in mapeamento_letras.items()}
        self.num_arestas_count = 0

    def numero_de_vertices(self):
        return self.num_vertices

    def numero_de_arestas(self):
        return self.num_arestas_count

    def sequencia_de_graus(self):
        graus = [sum(row) for row in self.adj_matrix]
        return graus

    def adicionar_aresta(self, u_letra, v_letra):
        u = self.mapeamento_letras[u_letra]
        v = self.mapeamento_letras[v_letra]
        if self.adj_matrix[u][v] == 0:
            self.adj_matrix[u][v] = 1
            self.adj_matrix[v][u] = 1
            self.num_arestas_count += 1
            print(f"Aresta adicionada entre {u_letra} e {v_letra}.")

    def remover_aresta(self, u_letra, v_letra):
        u = self.mapeamento_letras[u_letra]
        v = self.mapeamento_letras[v_letra]
        if self.adj_matrix[u][v] == 1:
            self.adj_matrix[u][v] = 0
            self.adj_matrix[v][u] = 0
            self.num_arestas_count -= 1
            print(f"Aresta removida entre {u_letra} e {v_letra}.")

    def imprimir(self):
        cabecalho = " ".join(self.mapeamento_letras.keys())
        print("  " + cabecalho)
        for i in range(self.num_vertices):
            # CORREÇÃO AQUI: Usar o dicionário inverso para obter a letra a partir do índice
            letra = self.mapeamento_letras_por_indice[i]
            linha = " ".join(map(str, self.adj_matrix[i]))
            print(f"{letra}| {linha}")