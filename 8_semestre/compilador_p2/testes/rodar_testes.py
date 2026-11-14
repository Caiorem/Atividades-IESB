"""
Bateria de testes do Compilador Bidu.

  corretos/  -> devem compilar; o código SML gerado é executado num simulador
                do Simpletron e a saída é comparada com a esperada.
  erros/     -> não podem compilar; confere se as fases de erro esperadas
                (Léxico, Sintático, Semântico, Síntese) foram reportadas.

Cada teste é rodado com e sem otimização.

Uso (de qualquer pasta):
    python testes/rodar_testes.py            -> roda tudo
    python testes/rodar_testes.py c04 e11    -> só os testes cujo nome começa assim
    python testes/rodar_testes.py -v         -> mostra também os erros reportados
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from compilador_simple import (compile_source, SML_OPCODES, SML_MEM_SIZE,  # noqa: E402
                               SML_WORD_MAX, div_trunc)

ERRO_EXECUCAO = 'erro de execução'

# arquivo -> lista de (entradas, saída esperada); a saída pode ser ERRO_EXECUCAO
CORRETOS = {
    'c01_soma.txt': [([3, 5], [8]), ([-4, 10], [6])],
    'c02_maior.txt': [([3, 7], [7]), ([9, 2], [9]), ([4, 4], [4])],
    'c03_soma_sentinela.txt': [([5, 3, 2, 0], [10]), ([0], [0])],
    'c04_fatorial.txt': [([5], [120]), ([0], [1]), ([1], [1]), ([7], [5040]), ([-3], [-1])],
    'c05_media.txt': [([4], [2]), ([5], [3]), ([0], [-1])],
    'c06_precedencia.txt': [([10, 3, 2], [16, 5, 15, 15])],
    'c07_negativos.txt': [([], [-5, 5, 1, -3, -1])],
    'c08_relacionais.txt': [([4, 4], [49]), ([2, 9], [22]), ([9, 2], [42])],
    'c09_resto_divisao.txt': [([17, 5], [2, 3]), ([20, 4], [0, 5]), ([-17, 5], [-2, -3])],
    'c10_goto_para_rem.txt': [([3], [3, 2, 1]), ([0], [])],
    'c11_fibonacci.txt': [([7], [0, 1, 1, 2, 3, 5, 8]), ([0], [])],
    'c12_programa_minimo.txt': [([], [])],
    'c13_variavel_sem_input.txt': [([], [1])],
    'c14_expressao_constante.txt': [([], [23, 7])],
    'c15_espacos_e_linhas_em_branco.txt': [([4], [8])],
    'c16_rem_livre.txt': [([42], [42])],
    'c17_potencia.txt': [([2, 10], [1024]), ([5, 0], [1])],
    'c18_valor_absoluto.txt': [([-8], [8]), ([5], [5]), ([0], [0])],
    'c19_limites_da_palavra.txt': [([], [9999, -9999])],
    'c20_divisao_por_zero.txt': [([7], ERRO_EXECUCAO)],
    # exercício passado pelo professor em aula (ordenar 3 números)
    'c21_ordena_tres.txt': [([5, 7, 4], [4, 5, 7]), ([1, 2, 3], [1, 2, 3]), ([3, 2, 1], [1, 2, 3]),
                            ([2, 3, 1], [1, 2, 3]), ([3, 1, 2], [1, 2, 3]), ([4, 4, 1], [1, 4, 4])],
}

# arquivo -> fases que precisam aparecer entre os erros reportados
ERROS = {
    'e01_maiuscula.txt': {'Léxico'},
    'e02_parenteses.txt': {'Léxico'},
    'e03_simbolo_invalido.txt': {'Léxico'},
    'e04_identificador_longo.txt': {'Léxico'},
    'e05_sem_numero_de_linha.txt': {'Sintático'},
    'e06_linhas_fora_de_ordem.txt': {'Sintático'},
    'e07_linha_duplicada.txt': {'Sintático'},
    'e08_comando_desconhecido.txt': {'Sintático'},
    'e09_if_sem_goto.txt': {'Sintático'},
    'e10_goto_sem_destino.txt': {'Sintático'},
    'e11_goto_linha_inexistente.txt': {'Semântico'},
    'e12_sem_end.txt': {'Semântico'},
    'e13_end_duplicado.txt': {'Semântico'},
    'e14_end_nao_e_ultimo.txt': {'Semântico'},
    'e15_end_com_parametro.txt': {'Sintático'},
    'e16_let_sem_igual.txt': {'Sintático'},
    'e17_expressao_incompleta.txt': {'Sintático'},
    'e18_operadores_seguidos.txt': {'Sintático'},
    'e19_input_duas_variaveis.txt': {'Sintático'},
    'e20_print_constante.txt': {'Sintático'},
    'e21_if_com_atribuicao.txt': {'Sintático'},
    'e22_constante_grande.txt': {'Síntese'},
    'e23_estouro_de_memoria.txt': {'Síntese'},
    'e24_varios_erros.txt': {'Léxico', 'Sintático', 'Semântico'},
    'e25_arquivo_vazio.txt': {'Semântico'},
}


# ==========================================
# SIMULADOR DO SIMPLETRON
# ==========================================

def simular(memoria, entradas, max_passos=100000):
    """Executa o código SML. Devolve a lista de saídas ou ERRO_EXECUCAO."""
    mem = list(memoria) + [0] * (SML_MEM_SIZE - len(memoria))
    op = {v: k for k, v in SML_OPCODES.items()}
    entradas = list(entradas)
    saida = []
    acc = 0
    pc = 0

    for _ in range(max_passos):
        if not 0 <= pc < SML_MEM_SIZE:
            return ERRO_EXECUCAO
        palavra = mem[pc]
        codigo, end = divmod(palavra, SML_MEM_SIZE)
        nome = op.get(codigo)
        pc += 1

        if nome == 'READ':
            if not entradas:
                return ERRO_EXECUCAO          # programa pediu mais entradas que o teste deu
            mem[end] = entradas.pop(0)
        elif nome == 'WRITE':
            saida.append(mem[end])
        elif nome == 'LOAD':
            acc = mem[end]
        elif nome == 'STORE':
            mem[end] = acc
        elif nome == 'ADD':
            acc += mem[end]
        elif nome == 'SUBTRACT':
            acc -= mem[end]
        elif nome == 'MULTIPLY':
            acc *= mem[end]
        elif nome == 'DIVIDE':
            if mem[end] == 0:
                return ERRO_EXECUCAO
            acc = div_trunc(acc, mem[end])
        elif nome == 'MOD':
            if mem[end] == 0:
                return ERRO_EXECUCAO
            acc = acc - div_trunc(acc, mem[end]) * mem[end]
        elif nome == 'BRANCH':
            pc = end
        elif nome == 'BRANCHNEG':
            if acc < 0:
                pc = end
        elif nome == 'BRANCHZERO':
            if acc == 0:
                pc = end
        elif nome == 'HALT':
            return saida
        else:
            return ERRO_EXECUCAO              # opcode inválido

        if abs(acc) > SML_WORD_MAX:
            return ERRO_EXECUCAO              # estouro do acumulador
    return ERRO_EXECUCAO                      # laço infinito


# ==========================================
# EXECUÇÃO DOS TESTES
# ==========================================

def ler(pasta, nome):
    with open(os.path.join(AQUI, pasta, nome), encoding='utf-8') as f:
        return f.read()


def testar_correto(nome, casos, verbose):
    codigo = ler('corretos', nome)
    falhas = []
    for otimizar in (True, False):
        modo = 'com otimização' if otimizar else 'sem otimização'
        try:
            erros, _, _, _, gerador = compile_source(codigo, otimizar)
        except Exception as ex:  # o compilador nunca deveria quebrar
            falhas.append(f"{modo}: exceção {type(ex).__name__}: {ex}")
            continue
        if gerador is None or erros.has_errors():
            falhas.append(f"{modo}: não compilou -> {erros.sorted()}")
            continue
        for entradas, esperado in casos:
            obtido = simular(gerador.memory, entradas)
            if obtido != esperado:
                falhas.append(f"{modo}: entrada {entradas} -> esperado {esperado}, obtido {obtido}")
    return falhas


def testar_erro(nome, fases, verbose):
    codigo = ler('erros', nome)
    try:
        erros, _, _, _, gerador = compile_source(codigo)
    except Exception as ex:
        return [f"exceção {type(ex).__name__}: {ex}"]
    if not erros.has_errors():
        return ["compilou sem erros, mas deveria falhar"]
    if verbose:
        for linha, col, fase, msg in erros.sorted():
            print(f"        [{fase}] linha {linha}, col {col}: {msg}")
    reportadas = {fase for _, _, fase, _ in erros.errors}
    faltando = fases - reportadas
    if faltando:
        return [f"fases esperadas {sorted(fases)}, reportadas {sorted(reportadas)}"]
    return []


def main():
    args = sys.argv[1:]
    verbose = '-v' in args
    filtros = [a for a in args if a != '-v']

    def selecionado(nome):
        return not filtros or any(nome.startswith(f) for f in filtros)

    # avisa se existir arquivo nas pastas sem resultado esperado cadastrado
    for pasta, tabela in (('corretos', CORRETOS), ('erros', ERROS)):
        for nome in sorted(os.listdir(os.path.join(AQUI, pasta))):
            if nome.endswith('.txt') and nome not in tabela:
                print(f"AVISO: {pasta}/{nome} não está cadastrado em rodar_testes.py")

    total = falhou = 0
    for pasta, tabela, testar in (('corretos', CORRETOS, testar_correto),
                                  ('erros', ERROS, testar_erro)):
        print(f"\n=== {pasta} ===")
        for nome, esperado in tabela.items():
            if not selecionado(nome):
                continue
            total += 1
            falhas = testar(nome, esperado, verbose)
            print(f"  {'OK   ' if not falhas else 'FALHA'} {nome}")
            for f in falhas:
                print(f"        {f}")
            falhou += bool(falhas)

    print(f"\n{total - falhou}/{total} testes passaram.")
    sys.exit(1 if falhou else 0)


if __name__ == '__main__':
    main()
