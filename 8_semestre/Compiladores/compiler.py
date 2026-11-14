# /*************************************************************************
#  * Autores: Caio Silveira e Mayron Malaquias  *
#  * Matrículas: 2312130166 e 2312130167        *
#  * Data: 2026-09-12                           *
#  *            Compilador Bidu                 *
#  *************************************************************************/

"""
Compilador para a Linguagem SIMPLE - Fases de Análise (Léxica, Sintática e Semântica)

Uso:
    python compilador_simple.py arquivo.simple      -> compila um único arquivo
    python compilador_simple.py                     -> compila todos os *.txt do diretório atual
"""

import os
import sys
import glob

KEYWORDS = {'rem', 'input', 'let', 'print', 'goto', 'if', 'end'}
ARITH_OPS = {'+', '-', '*', '/', '%'}


# ==========================================
# 0. COLETOR DE ERROS
# ==========================================

class ErrorCollector:
    """Acumula erros de todas as fases sem interromper a análise."""

    def __init__(self):
        # cada erro: (linha_fisica_ou_None, coluna_ou_None, fase, mensagem)
        self.errors = []

    def add(self, line, col, phase, msg):
        self.errors.append((line, col, phase, msg))

    def has_errors(self):
        return len(self.errors) > 0

    def sorted(self):
        def key(e):
            line = e[0] if e[0] is not None else float('inf')
            col = e[1] if e[1] is not None else -1
            return (line, col)
        return sorted(self.errors, key=key)


# ==========================================
# 1. ANALISADOR LÉXICO (SCANNER)
# ==========================================

class Token:
    def __init__(self, type_, value, line_num, col):
        self.type = type_
        self.value = value
        self.line_num = line_num
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"


def tokenize_line(raw_line, line_num, errors):
    """
    Tokeniza uma linha física do arquivo-fonte.

    IMPORTANTE: recebe a linha ORIGINAL (sem strip), para que as colunas
    reportadas correspondam exatamente à posição no arquivo.

    Ao encontrar um caractere inválido, registra o erro no coletor e
    continua tokenizando o restante da linha, em vez de abortar — isso
    permite capturar mais de um erro léxico na mesma linha.
    """
    tokens = []
    i = 0
    n = len(raw_line)

    while i < n:
        c = raw_line[i]

        if c.isspace():
            i += 1
            continue

        col = i + 1

        # Caracteres maiúsculos são proibidos fora de 'rem'
        if c.isupper():
            errors.add(line_num, col, 'Léxico',
                       f"caractere maiúsculo '{c}' não é permitido na linguagem SIMPLE.")
            i += 1
            continue

        # Constantes numéricas inteiras
        if c.isdigit():
            start = i
            while i < n and raw_line[i].isdigit():
                i += 1
            num_val = int(raw_line[start:i])
            tokens.append(Token('INT', num_val, line_num, start + 1))
            continue

        # Palavras reservadas ou variáveis
        if c.isalpha() and c.islower():
            start = i
            while i < n and raw_line[i].isalpha() and raw_line[i].islower():
                i += 1
            word = raw_line[start:i]

            if word in KEYWORDS:
                tokens.append(Token('KEYWORD', word, line_num, start + 1))
                if word == 'rem':
                    # Resto da linha é documentação; ignorado pelo compilador
                    break
            elif len(word) == 1:
                tokens.append(Token('VAR', word, line_num, start + 1))
            else:
                errors.add(line_num, start + 1, 'Léxico',
                           f"identificador '{word}' inválido: variáveis devem ter "
                           f"exatamente 1 letra minúscula.")
            continue

        # Operadores relacionais com 2 caracteres
        if raw_line[i:i + 2] in {'==', '!=', '>=', '<='}:
            tokens.append(Token('RELOP', raw_line[i:i + 2], line_num, col))
            i += 2
            continue

        # Operadores relacionais com 1 caractere
        if c in {'>', '<'}:
            tokens.append(Token('RELOP', c, line_num, col))
            i += 1
            continue

        # Atribuição '='
        if c == '=':
            tokens.append(Token('ASSIGN', '=', line_num, col))
            i += 1
            continue

        # Operadores aritméticos
        if c in ARITH_OPS:
            tokens.append(Token('ARITHOP', c, line_num, col))
            i += 1
            continue

        # Se não bater em nenhum dos casos acima, é um símbolo inválido.
        # Ou seja, as regras acima são as únicas permitidas, as demais são inválidas.
        errors.add(line_num, col, 'Léxico', f"símbolo inválido '{c}'.")
        i += 1

    return tokens


# ==========================================
# 2. ANALISADOR SINTÁTICO (PARSER)
# ==========================================

class Parser:
    def __init__(self, raw_code, errors):
        self.raw_code = raw_code
        self.errors = errors
        # cada item: (numero_linha_simple, comando, argumento, linha_fisica)
        # mantido por compatibilidade / checagens simples (ex.: contagem de 'end')
        self.program_lines = []
        # cada item: dict com os dados completos da instrução, usado pelo Interpreter
        self.instructions = []
        self.defined_line_numbers = set()
        # cada item: (linha_destino, linha_fisica_origem, numero_linha_simple_origem)
        self.jump_targets = []
        self.last_simple_line = None

    def parse(self):
        lines = self.raw_code.splitlines()
        for phys_idx, raw_line in enumerate(lines, start=1):
            if not raw_line.strip():
                continue

            tokens = tokenize_line(raw_line, phys_idx, self.errors)
            if not tokens:
                # A linha só continha erros léxicos; nada para o parser analisar.
                continue

            self._parse_instruction(tokens, phys_idx)

    def _parse_instruction(self, tokens, phys_idx):
        error_count_before = len(self.errors.errors)
        first_tok = tokens[0]
        simple_line_no = None

        if first_tok.type != 'INT':
            self.errors.add(phys_idx, first_tok.col, 'Sintático',
                            "a instrução deve começar com um número de linha.")
        else:
            simple_line_no = first_tok.value
            self.defined_line_numbers.add(simple_line_no)

            if self.last_simple_line is not None and simple_line_no <= self.last_simple_line:
                self.errors.add(phys_idx, first_tok.col, 'Sintático',
                                f"número de linha {simple_line_no} fora de ordem crescente "
                                f"(linha anterior: {self.last_simple_line}).")
            self.last_simple_line = simple_line_no

            if len(tokens) < 2:
                self.errors.add(phys_idx, first_tok.col, 'Sintático',
                                f"instrução {simple_line_no}: comando ausente após o número de linha.")
            else:
                cmd_tok = tokens[1]
                if cmd_tok.type != 'KEYWORD':
                    self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                    f"instrução {simple_line_no}: era esperado um comando reservado "
                                    f"(rem, input, let, print, goto, if, end).")
                else:
                    self._parse_command(simple_line_no, phys_idx, cmd_tok, tokens[2:])

        # Recuperação de erro: Tinha visto que estava parando no erro inicial e não pegando todos os erros
        # a depender da sequência e quais erros. Inditifiquei isso em um erro de goto para uma linha 
        # inexistente, que não estava sendo reportado. Solução: def _scan_for_jump_targets
        if simple_line_no is not None and len(self.errors.errors) > error_count_before:
            self._scan_for_jump_targets(tokens[1:], phys_idx, simple_line_no)

    def _scan_for_jump_targets(self, tokens, phys_idx, line_no):
        for i in range(len(tokens) - 1):
            t = tokens[i]
            nxt = tokens[i + 1]
            if t.type == 'KEYWORD' and t.value == 'goto' and nxt.type == 'INT':
                self.jump_targets.append((nxt.value, phys_idx, line_no))

    def _parse_command(self, line_no, phys_idx, cmd_tok, args):
        cmd = cmd_tok.value

        if cmd == 'rem':
            self.program_lines.append((line_no, 'rem', None, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'rem'})

        elif cmd == 'input':
            if len(args) != 1 or args[0].type != 'VAR':
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: comando 'input' requer exatamente "
                                f"1 variável.")
                return
            self.program_lines.append((line_no, 'input', args[0].value, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'input', 'var': args[0].value})

        elif cmd == 'print':
            if len(args) != 1 or args[0].type != 'VAR':
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: comando 'print' requer exatamente "
                                f"1 variável.")
                return
            self.program_lines.append((line_no, 'print', args[0].value, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'print', 'var': args[0].value})

        elif cmd == 'goto':
            if len(args) != 1 or args[0].type != 'INT':
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: comando 'goto' requer o número de "
                                f"linha de destino.")
                return
            self.jump_targets.append((args[0].value, phys_idx, line_no))
            self.program_lines.append((line_no, 'goto', args[0].value, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'goto', 'dest': args[0].value})

        elif cmd == 'end':
            if len(args) != 0:
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: comando 'end' não recebe parâmetros.")
                return
            self.program_lines.append((line_no, 'end', None, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'end'})

        elif cmd == 'let':
            if len(args) < 3 or args[0].type != 'VAR' or args[1].type != 'ASSIGN':
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: sintaxe inválida no comando 'let' "
                                f"(esperado: let <var> = <expressão>).")
                return

            expr_tokens = args[2:]
            expect_op = False
            valid = True
            for tok in expr_tokens:
                if not expect_op:
                    if tok.type not in ('VAR', 'INT'):
                        self.errors.add(phys_idx, tok.col, 'Sintático',
                                        f"instrução {line_no}: operando inválido na expressão.")
                        valid = False
                        break
                    expect_op = True
                else:
                    if tok.type != 'ARITHOP':
                        self.errors.add(phys_idx, tok.col, 'Sintático',
                                        f"instrução {line_no}: operador aritmético esperado.")
                        valid = False
                        break
                    expect_op = False

            if valid and not expect_op:
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: expressão aritmética incompleta.")
                valid = False

            if valid:
                self.program_lines.append((line_no, 'let', args[0].value, phys_idx))
                self.instructions.append({'line': line_no, 'cmd': 'let',
                                          'var': args[0].value, 'expr': expr_tokens})

        elif cmd == 'if':
            if len(args) != 5:
                self.errors.add(phys_idx, cmd_tok.col, 'Sintático',
                                f"instrução {line_no}: estrutura incompleta no 'if/goto' "
                                f"(esperado: if <op> <relop> <op> goto <linha>).")
                return
            op1, rel, op2, kw_goto, dest = args
            if op1.type not in ('VAR', 'INT') or rel.type != 'RELOP' or op2.type not in ('VAR', 'INT'):
                self.errors.add(phys_idx, op1.col, 'Sintático',
                                f"instrução {line_no}: condição relacional inválida.")
                return
            if kw_goto.type != 'KEYWORD' or kw_goto.value != 'goto':
                self.errors.add(phys_idx, kw_goto.col, 'Sintático',
                                f"instrução {line_no}: era esperado 'goto' após a condição do 'if'.")
                return
            if dest.type != 'INT':
                self.errors.add(phys_idx, dest.col, 'Sintático',
                                f"instrução {line_no}: o destino após 'goto' deve ser um número de linha.")
                return
            self.jump_targets.append((dest.value, phys_idx, line_no))
            self.program_lines.append((line_no, 'if/goto', dest.value, phys_idx))
            self.instructions.append({'line': line_no, 'cmd': 'if',
                                      'op1': op1, 'rel': rel.value, 'op2': op2,
                                      'dest': dest.value})


# ==========================================
# 3. ANALISADOR SEMÂNTICO
# ==========================================

class SemanticAnalyzer:
    def __init__(self, parser, errors):
        self.parser = parser
        self.errors = errors

    def analyze(self):
        defined_lines = self.parser.defined_line_numbers

        # Regra Semântica 1: todo goto/if-goto deve desviar para uma linha existente
        for dest, phys_line, simple_line in self.parser.jump_targets:
            if dest not in defined_lines:
                self.errors.add(phys_line, None, 'Semântico',
                                f"instrução {simple_line}: desvio para a linha {dest}, "
                                f"que não existe no programa.")

        if not self.parser.program_lines:
            return

        # Regra Semântica 2: validação do comando 'end'
        commands = [c[1] for c in self.parser.program_lines]
        end_count = commands.count('end')

        if end_count == 0:
            self.errors.add(None, None, 'Semântico', "o programa não possui o comando 'end'.")
        elif end_count > 1:
            self.errors.add(None, None, 'Semântico',
                            "o comando 'end' aparece mais de uma vez no programa.")
        elif self.parser.program_lines[-1][1] != 'end':
            last_phys_line = self.parser.program_lines[-1][3]
            self.errors.add(last_phys_line, None, 'Semântico',
                            "o comando 'end' deve ser a última instrução do programa.")


# ==========================================
# 4. DUMP DE TOKENS NO FORMATO OFICIAL DA DISCIPLINA
#    [código, valor, (linha, coluna)]
# ==========================================

# Tabela de códigos de token conforme o material da disciplina
_KEYWORD_CODES = {'rem': 61, 'input': 62, 'let': 63, 'print': 64,
                   'goto': 65, 'if': 66, 'end': 67}
_ARITHOP_CODES = {'+': 21, '-': 22, '*': 23, '/': 24, '%': 25}
_RELOP_CODES = {'==': 31, '!=': 32, '>': 33, '<': 34, '>=': 35, '<=': 36}


def token_code(tok):
    """Retorna o código numérico oficial de um token, conforme a tabela
    da disciplina (delimitadores, operadores, identificadores, constantes
    e palavras reservadas)."""
    if tok.type == 'KEYWORD':
        return _KEYWORD_CODES[tok.value]
    if tok.type == 'VAR':
        return 41
    if tok.type == 'INT':
        return 51
    if tok.type == 'ASSIGN':
        return 11
    if tok.type == 'ARITHOP':
        return _ARITHOP_CODES[tok.value]
    if tok.type == 'RELOP':
        return _RELOP_CODES[tok.value]
    raise ValueError(f"tipo de token sem código definido: {tok.type}")


def dump_tokens(raw_code):
    """
    Imprime o fluxo de tokens no formato [código, valor, (linha, coluna)],
    igual ao exemplo do material da disciplina: LF (10) ao final de cada
    linha, ETX (3) ao final do arquivo, e 'valor' sendo o índice do lexema
    numa tabela compartilhada entre constantes e identificadores (o mesmo
    índice é reaproveitado se o mesmo valor reaparecer no programa).

    Este dump é apenas uma ferramenta de conferência visual — não participa
    da detecção de erros sintáticos/semânticos.
    """
    literal_table = {}
    literal_order = []

    def literal_index(value):
        key = str(value)
        if key not in literal_table:
            literal_table[key] = len(literal_order)
            literal_order.append(key)
        return literal_table[key]

    lines = [l for l in raw_code.splitlines() if l.strip()]
    dummy_errors = ErrorCollector()  # não usamos os erros aqui, só tokens

    for i, raw_line in enumerate(lines):
        phys_idx = i + 1
        tokens = tokenize_line(raw_line, phys_idx, dummy_errors)

        parts = []
        for tok in tokens:
            code = token_code(tok)
            value_field = literal_index(tok.value) if tok.type in ('INT', 'VAR') else ''
            parts.append(f"[{code}, {value_field}, ({tok.line_num}, {tok.col})]")

        is_last_line = (i == len(lines) - 1)
        end_code = 3 if is_last_line else 10  # ETX no fim do arquivo, LF nas demais
        end_col = len(raw_line.rstrip()) + 1
        parts.append(f"[{end_code}, , ({phys_idx}, {end_col})]")

        print(''.join(parts))

    print("\nTabela de constantes/identificadores:")
    for idx, lex in enumerate(literal_order):
        print(f"{idx} : {lex}")


def compile_file(filepath):
    filename = os.path.basename(filepath)
    print("=" * 60)
    print(" /\\_/\\ ") 
    print("( o.o )  COMPILADOR BIDU")
    print(" ,,,,, \n")
    print(f"COMPILANDO ARQUIVO: {filename}")
    print("=" * 60)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except OSError as err:
        print(f">> ERRO AO ABRIR ARQUIVO: {err}\n")
        return

    errors = ErrorCollector()

    parser = Parser(code, errors)
    parser.parse()

    semantic = SemanticAnalyzer(parser, errors)
    semantic.analyze()

    if errors.has_errors():
        print(f">> STATUS: {len(errors.errors)} INCONSISTÊNCIA(S) DETECTADA(S)")
        for line, col, phase, msg in errors.sorted():
            loc = f"linha {line}" if line is not None else "programa"
            if col is not None:
                loc += f", col {col}"
            print(f"   [{phase}] {loc}: {msg}")
    else:
        print(">> STATUS: SUCESSO")
        print("   O código-fonte é válido (Léxico, Sintático e Semântico OK).")

    print()


if __name__ == '__main__':
    args = sys.argv[1:]
    show_tokens = '--tokens' in args
    files = [a for a in args if a != '--tokens']

    if show_tokens:
        # Modo de conferência: só mostra o fluxo de tokens, formato oficial da disciplina.
        # python compilador_simple.py arquivo.simple --tokens
        if not files:
            print("Informe um arquivo: python compilador_simple.py arquivo.simple --tokens")
        else:
            with open(files[0], 'r', encoding='utf-8') as f:
                dump_tokens(f.read())
    elif files:
        # Modo "gcc-like": python compilador_simple.py arquivo.simple
        compile_file(files[0])
    else:
        # Modo lote: compila todos os .txt do diretório atual (útil para testes)
        txt_files = sorted(glob.glob("*.txt"))
        if not txt_files:
            print("Nenhum arquivo .txt encontrado no diretório atual e "
                  "nenhum arquivo foi passado como argumento!")
        else:
            print(f"Iniciando compilação de {len(txt_files)} arquivo(s) de teste...\n")
            for f in txt_files:
                compile_file(f)