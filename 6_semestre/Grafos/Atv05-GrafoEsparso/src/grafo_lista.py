import sys
from grafo_interface import Grafo

class GrafoListaAdjacencia(Grafo):
    def __init__(self):
        self.lista_adjacencia = {}
        self.numero_de_no = 0

    
    def adicionar_no(self, no):
        if no not in self.lista_adjacencia:
            self.lista_adjacencia[no] = []
            self.numero_de_no += 1
    

    def numero_de_vertices(self):
        return self.numero_de_no


    def numero_de_aresta(self):
        # print(self.matriz)
        contador = 0
        for i in self.lista_adjacencia:
            for j in self.lista_adjacencia[i]:
                contador += 1
                
        return int(contador / 2)


    def sequencia_de_graus(self):
        # print(self.matriz)
        list_sequence = []
        contador = 0
        for i in self.lista_adjacencia:
            for j in self.lista_adjacencia[i]:
                contador += 1
            list_sequence.append(contador)
            contador = 0
        return list_sequence


    def remover_aresta(self, v1, v2):
        if v1 in self.lista_adjacencia and v2 in self.lista_adjacencia:
            self.lista_adjacencia[v1].remove(v2)
            #self.lista_adjacencia[v2].remove(v1)
            print(f"Aresta removida entre {v1} e {v2}")
        else:
            print("Não existe um dos vertices no grafo")

    def adicionar_aresta(self, v1,v2):
        if v1 in self.lista_adjacencia and v2 in self.lista_adjacencia:
            self.lista_adjacencia[v1].append(v2)
            self.lista_adjacencia[v2].append(v1)
            print(f"Aresta adicionada entre {v1} e {v2}")
        else:
            print("Não existe um dos vertices no grafo")
    
    def imprimir(self):
        print("Lista de Adjacencia")
        for no, vizinho in self.lista_adjacencia.items():
            print(f"{no} -> [ {vizinho}]")