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

Diferente da versão anterior, este compilador NÃO para no primeiro erro
encontrado. Cada fase registra seus erros em um coletor central e continua
a análise, permitindo reportar múltiplas inconsistências no mesmo arquivo
e, quando aplicável, mais de um erro na mesma linha (ex.: um símbolo léxico
inválido e um erro de estrutura sintática na mesma instrução).
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

        # Recuperação de erro: se a instrução falhou por algum motivo, ainda assim
        # tentamos localizar um padrão "goto <número>" nos tokens restantes, para
        # que um destino de desvio inexistente seja capturado na análise semântica
        # mesmo quando a instrução como um todo é sintaticamente inválida.
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
# 4. INTERPRETADOR (EXECUÇÃO DO PROGRAMA VALIDADO)
# ==========================================

class RuntimeErrorSimple(Exception):
    pass


class Interpreter:
    """
    Executa um programa SIMPLE já validado (léxico + sintático + semântico OK).
    O desvio de fluxo (goto / if-goto) usa o número de linha DECLARADO no
    programa-fonte (ex.: 35, 65), não a linha física do arquivo.
    """

    MAX_STEPS = 1_000_000  # trava de segurança contra loop infinito

    def __init__(self, instructions):
        self.instructions = instructions
        self.line_index = {instr['line']: idx for idx, instr in enumerate(instructions)}
        self.vars = {}

    def _value_of(self, token):
        return token.value if token.type == 'INT' else self.vars.get(token.value, 0)

    def _eval_expr(self, expr_tokens):
        """Avalia uma expressão aritmética respeitando precedência
        (*, /, % antes de +, -) e associatividade à esquerda."""
        values = [self._value_of(expr_tokens[0])]
        ops = []
        i = 1
        while i < len(expr_tokens):
            ops.append(expr_tokens[i].value)
            values.append(self._value_of(expr_tokens[i + 1]))
            i += 2

        # 1ª passada: multiplicação, divisão inteira e resto
        idx = 0
        while idx < len(ops):
            if ops[idx] in ('*', '/', '%'):
                a, b = values[idx], values[idx + 1]
                if ops[idx] == '*':
                    r = a * b
                else:
                    if b == 0:
                        raise RuntimeErrorSimple("divisão por zero.")
                    r = int(a / b) if ops[idx] == '/' else a - b * int(a / b)
                values[idx:idx + 2] = [r]
                ops.pop(idx)
            else:
                idx += 1

        # 2ª passada: soma e subtração, esquerda para direita
        result = values[0]
        for op, val in zip(ops, values[1:]):
            result = result + val if op == '+' else result - val
        return result

    def _eval_relation(self, op1, rel, op2):
        a, b = self._value_of(op1), self._value_of(op2)
        return {
            '==': a == b, '!=': a != b,
            '>': a > b, '<': a < b,
            '>=': a >= b, '<=': a <= b,
        }[rel]

    def run(self):
        pc = 0
        steps = 0
        while 0 <= pc < len(self.instructions):
            steps += 1
            if steps > self.MAX_STEPS:
                raise RuntimeErrorSimple(
                    f"número máximo de passos ({self.MAX_STEPS}) excedido — "
                    f"possível loop infinito no programa.")

            instr = self.instructions[pc]
            cmd = instr['cmd']

            if cmd == 'rem':
                pc += 1

            elif cmd == 'input':
                raw = input('? ')
                try:
                    self.vars[instr['var']] = int(raw)
                except ValueError:
                    raise RuntimeErrorSimple(
                        f"instrução {instr['line']}: valor inteiro esperado em 'input', "
                        f"recebido '{raw}'.")
                pc += 1

            elif cmd == 'let':
                self.vars[instr['var']] = self._eval_expr(instr['expr'])
                pc += 1

            elif cmd == 'print':
                print(self.vars.get(instr['var'], 0))
                pc += 1

            elif cmd == 'goto':
                pc = self.line_index[instr['dest']]

            elif cmd == 'if':
                if self._eval_relation(instr['op1'], instr['rel'], instr['op2']):
                    pc = self.line_index[instr['dest']]
                else:
                    pc += 1

            elif cmd == 'end':
                return

            else:
                pc += 1


# ==========================================
# ROTINA PRINCIPAL
# ==========================================

def compile_file(filepath, run_program=False):
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
        print()
        return

    print(">> STATUS: SUCESSO")
    print("   O código-fonte é válido (Léxico, Sintático e Semântico OK).")

    if run_program:
        print("-" * 60)
        print("EXECUÇÃO:")
        try:
            Interpreter(parser.instructions).run()
        except RuntimeErrorSimple as err:
            print(f">> ERRO DE EXECUÇÃO: {err}")

    print()


if __name__ == '__main__':
    args = sys.argv[1:]
    run_program = '--run' in args
    files = [a for a in args if a != '--run']

    if files:
        # Modo "gcc-like": python compilador_simple.py arquivo.simple [--run]
        compile_file(files[0], run_program=run_program)
    else:
        # Modo lote: compila todos os .txt do diretório atual (útil para testes)
        txt_files = sorted(glob.glob("*.txt"))
        if not txt_files:
            print("Nenhum arquivo .txt encontrado no diretório atual e "
                  "nenhum arquivo foi passado como argumento!")
        else:
            print(f"Iniciando compilação de {len(txt_files)} arquivo(s) de teste...\n")
            for f in txt_files:
                compile_file(f, run_program=run_program)