# main.py

from grafo_matriz import GrafoMatrizAdjacencia

def main():
    # O mapeamento dos vértices para reproduzir a saída da imagem
    mapeamento_letras = {
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4
    }
    
    # Invertendo o mapeamento para facilitar a busca por índice
    # Esta parte é redundante e pode ser removida no futuro,
    # mas o código funciona assim também
    mapeamento_indices = {i: letra for letra, i in mapeamento_letras.items()}
    num_vertices = len(mapeamento_letras)

    # Cria a instância do grafo
    meu_grafo = GrafoMatrizAdjacencia(num_vertices, mapeamento_letras)

    # Adiciona as arestas
    meu_grafo.adicionar_aresta('A', 'B')
    meu_grafo.adicionar_aresta('A', 'C')
    meu_grafo.adicionar_aresta('C', 'D')
    meu_grafo.adicionar_aresta('C', 'E')
    meu_grafo.adicionar_aresta('B', 'D')
    
    # Imprime os resultados antes da remoção
    print("\nMatriz de Adjacência:")
    meu_grafo.imprimir()
    print(f"\nNúmero de vértices: {meu_grafo.numero_de_vertices()}")
    print(f"Número de arestas: {meu_grafo.numero_de_arestas()}")
    print(f"Sequência de graus: {meu_grafo.sequencia_de_graus()}")
    
    # Remove a aresta e imprime os novos resultados
    print("")
    meu_grafo.remover_aresta('A', 'C')
    
    print("\nMatriz de Adjacência:")
    meu_grafo.imprimir()

if __name__ == "__main__":
    main()