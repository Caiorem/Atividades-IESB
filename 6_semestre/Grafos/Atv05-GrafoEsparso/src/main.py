import sys
from abc import ABC, abstractmethod

class Grafo(ABC):
    @abstractmethod
    def numero_de_vertices(self):
        pass

    @abstractmethod
    def numero_de_arestas(self):
        pass

    @abstractmethod
    def sequencia_de_graus(self):
        pass

    @abstractmethod
    def adicionar_aresta(self, u, v):
        pass

    @abstractmethod
    def remover_aresta(self, u, v):
        pass

    @abstractmethod
    def imprimir(self):
        pass

class GrafoEsparso(Grafo):
    def __init__(self, vertices):
        self.vertices = sorted(list(set(vertices)))
        self.adj = {v: [] for v in self.vertices}
        self.num_arestas = 0

    def numero_de_vertices(self):
        return len(self.vertices)

    def numero_de_arestas(self):
        return self.num_arestas

    def sequencia_de_graus(self):
        graus = [len(self.adj[v]) for v in self.vertices]
        return sorted(graus)

    def adicionar_aresta(self, u, v):
        if u in self.adj and v in self.adj:
            self.adj[u].append(v)
            self.adj[v].append(u)
            self.num_arestas += 1
            print(f"Aresta adicionada entre {u} e {v}")
        else:
            print(f"Vértices {u} ou {v} não existem no grafo.")

    def remover_aresta(self, u, v):
        if u in self.adj and v in self.adj:
            if v in self.adj[u] and u in self.adj[v]:
                self.adj[u].remove(v)
                self.adj[v].remove(u)
                self.num_arestas -= 1
                print(f"Aresta removida entre {u} e {v}.")
            else:
                print(f"Não há aresta entre {u} e {v} para ser removida.")
        else:
            print(f"Vértices {u} ou {v} não existem no grafo.")

    def imprimir(self):
        print("\nLista de Adjacências:")
        for v in self.vertices:
            print(f"{v} -> {self.adj[v]}")
        print("\nNúmero de vértices:", self.numero_de_vertices())
        print("Número de arestas:", self.numero_de_arestas())
        print("Sequência de graus:", self.sequencia_de_graus())

vertices_do_grafo = ['A', 'B', 'C', 'D', 'E']
grafo = GrafoEsparso(vertices_do_grafo)

grafo.adicionar_aresta('A', 'B')
grafo.adicionar_aresta('A', 'C')
grafo.adicionar_aresta('A', 'C')
grafo.adicionar_aresta('C', 'D')
grafo.adicionar_aresta('C', 'E')
grafo.adicionar_aresta('B', 'D')

print("\nLista de Adjacências:")
for v in grafo.vertices:
    print(f"{v} -> {grafo.adj[v]}")
print("\nNúmero de vértices:", grafo.numero_de_vertices())
print("Número de arestas:", grafo.numero_de_arestas())
print("Sequência de graus:", grafo.sequencia_de_graus())

print(f"Aresta removida entre A e C.")
grafo.remover_aresta('A', 'C')


print("\nLista de Adjacências:")
for v in grafo.vertices:
    print(f"{v} -> {grafo.adj[v]}")