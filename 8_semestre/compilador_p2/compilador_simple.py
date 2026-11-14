# /*************************************************************************
#  * Autores: Caio Silveira e Mayron Malaquias  *
#  * Matrículas: 2312130166 e 2312130167        *
#  * Data: 2026-11-08                           *
#  *            Compilador Bidu                 *
#  *************************************************************************/

"""
Compilador Bidu para a Linguagem SIMPLE -> Simpletron Machine Language (SML)

Fases:
  ANÁLISE  : léxica, sintática e semântica (reporta TODOS os erros)
  SÍNTESE  : código intermediário (três endereços) -> otimização -> código SML

A síntese só é executada se a análise não encontrar nenhuma inconsistência.

Uso:
    python compilador_simple.py                            -> lê source.txt e gera binary.txt
    python compilador_simple.py prog.simple                -> gera prog.sml
    python compilador_simple.py prog.simple -o saida.sml   -> nome de saída explícito
    python compilador_simple.py prog.simple --ir           -> mostra o código intermediário
                                                             (antes e depois da otimização)
    python compilador_simple.py prog.simple --asm          -> mostra a listagem SML comentada
    python compilador_simple.py prog.simple --no-opt       -> desliga todas as otimizações
    python compilador_simple.py prog.simple --tokens       -> fluxo de tokens (formato da disciplina)
"""

import os
import sys

KEYWORDS = {'rem', 'input', 'let', 'print', 'goto', 'if', 'end'}
ARITH_OPS = {'+', '-', '*', '/', '%'}


# ==========================================
# CONFIGURAÇÃO DA MÁQUINA ALVO (SIMPLETRON)
# ------------------------------------------
# Tudo que depende da especificação do interpretador SML do professor
# está concentrado aqui. Se ele usar palavras de 6 dígitos ou tiver um
# opcode de resto, basta ajustar esta seção.
# ==========================================

SML_OPCODE_DIGITS = 2        # palavra +OOEE -> 2 dígitos de opcode
SML_ADDR_DIGITS = 2          # ... e 2 dígitos de endereço
SML_MEM_SIZE = 10 ** SML_ADDR_DIGITS                         # 100 posições (00-99)
SML_WORD_MAX = 10 ** (SML_OPCODE_DIGITS + SML_ADDR_DIGITS) - 1   # 9999

SML_OPCODES = {
    'READ': 10, 'WRITE': 11,
    'LOAD': 20, 'STORE': 21,
    'ADD': 30, 'SUBTRACT': 31, 'DIVIDE': 32, 'MULTIPLY': 33,
    # 'MOD': 34,   # descomente se o Simpletron do professor tiver resto
    'BRANCH': 40, 'BRANCHNEG': 41, 'BRANCHZERO': 42, 'HALT': 43,
}

SML_OUTPUT_PLUS_SIGN = True  # escreve "+1007" (True) ou "1007" (False)
SML_OUTPUT_SENTINEL = None   # ex.: -99999 se o carregador exigir sentinela no final
SML_DATA_AFTER_CODE = True   # dados logo após o código (True) ou a partir do fim da memória (False)
SML_OUTPUT_ONLY_USED = True  # grava só as palavras usadas (True) ou as 100 posições (False)


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

    def report(self):
        print(f">> STATUS: {len(self.errors)} INCONSISTÊNCIA(S) DETECTADA(S)")
        for line, col, phase, msg in self.sorted():
            loc = f"linha {line}" if line is not None else "programa"
            if col is not None:
                loc += f", col {col}"
            print(f"   [{phase}] {loc}: {msg}")


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

    Recebe a linha ORIGINAL (sem strip), para que as colunas reportadas
    correspondam exatamente à posição no arquivo. Ao encontrar um caractere
    inválido, registra o erro e continua, para capturar mais de um erro
    léxico na mesma linha.
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
            tokens.append(Token('INT', int(raw_line[start:i]), line_num, start + 1))
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
                    break   # resto da linha é comentário
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

        if c == '=':
            tokens.append(Token('ASSIGN', '=', line_num, col))
            i += 1
            continue

        if c in ARITH_OPS:
            tokens.append(Token('ARITHOP', c, line_num, col))
            i += 1
            continue

        errors.add(line_num, col, 'Léxico', f"símbolo inválido '{c}'.")
        i += 1

    return tokens


def fold_negative_literals(tokens):
    """
    Junta '-' seguido de constante em uma constante negativa quando o '-'
    está na posição de operando (início, ou após '=', operador ou relacional):
    "let f = -1" e "if x < -5 goto 10". Em "a - 1" o '-' continua binário.
    """
    out = []
    for tok in tokens:
        prev = out[-2] if len(out) >= 2 else None
        if (tok.type == 'INT' and out and out[-1].type == 'ARITHOP' and out[-1].value == '-'
                and (prev is None or prev.type not in ('VAR', 'INT'))):
            minus = out.pop()
            out.append(Token('INT', -tok.value, tok.line_num, minus.col))
        else:
            out.append(tok)
    return out


# ==========================================
# 2. ANALISADOR SINTÁTICO (PARSER)
# ==========================================

# Precedência dos operadores aritméticos (maior número = maior precedência)
PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}


def build_expr_tree(expr_tokens):
    """
    Converte a expressão infixa (já validada como operando op operando ...)
    em uma árvore sintática, usando o algoritmo shunting-yard de Dijkstra.

    Nós da árvore:
        ('num', valor)          constante inteira
        ('var', nome)           variável
        ('bin', op, esq, dir)   operação binária

    Usar '>=' no laço garante a associatividade à esquerda:
    a - b - c vira (a - b) - c.
    """
    operands = []
    operators = []

    def reduce_top():
        op = operators.pop()
        right = operands.pop()
        left = operands.pop()
        operands.append(('bin', op, left, right))

    for tok in expr_tokens:
        if tok.type == 'INT':
            operands.append(('num', tok.value))
        elif tok.type == 'VAR':
            operands.append(('var', tok.value))
        else:
            while operators and PRECEDENCE[operators[-1]] >= PRECEDENCE[tok.value]:
                reduce_top()
            operators.append(tok.value)

    while operators:
        reduce_top()
    return operands[0]


def tree_to_postfix(node):
    """Notação pós-fixa da árvore (apenas para exibição/conferência)."""
    if node[0] == 'num' or node[0] == 'var':
        return str(node[1])
    _, op, left, right = node
    return f"{tree_to_postfix(left)} {tree_to_postfix(right)} {op}"


class Parser:
    def __init__(self, raw_code, errors):
        self.raw_code = raw_code
        self.errors = errors
        # cada item: (numero_linha_simple, comando, argumento, linha_fisica)
        self.program_lines = []
        # cada item: dict com os dados completos da instrução (usado pela síntese)
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
                continue   # linha só com erros léxicos

            self._parse_instruction(tokens, phys_idx)

    def _parse_instruction(self, tokens, phys_idx):
        instr_count_before = len(self.instructions)
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
                    self._parse_command(simple_line_no, phys_idx, cmd_tok,
                                        fold_negative_literals(tokens[2:]))

        if len(self.instructions) > instr_count_before:
            # guarda a linha física para mensagens de erro da síntese
            self.instructions[-1]['phys'] = phys_idx
        elif simple_line_no is not None:
            # Recuperação de erro: instrução inválida, mas que contém
            # "goto <número>" -> registra o destino para a análise semântica.
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
                                          'var': args[0].value,
                                          'expr': expr_tokens,
                                          'tree': build_expr_tree(expr_tokens)})

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

        # Regra 1: todo goto/if-goto deve desviar para uma linha existente
        for dest, phys_line, simple_line in self.parser.jump_targets:
            if dest not in defined_lines:
                self.errors.add(phys_line, None, 'Semântico',
                                f"instrução {simple_line}: desvio para a linha {dest}, "
                                f"que não existe no programa.")

        if not self.parser.program_lines:
            return

        # Regra 2: validação do comando 'end'
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

        # Regra 3: constantes precisam caber em uma palavra do Simpletron
        for ins in self.parser.instructions:
            for value in _constants_of(ins):
                if abs(value) > SML_WORD_MAX:
                    self.errors.add(ins.get('phys'), None, 'Síntese',
                                    f"instrução {ins['line']}: constante {value} excede o "
                                    f"limite da palavra do Simpletron ({SML_WORD_MAX}).")


def _constants_of(ins):
    """Constantes usadas como operando (não conta destinos de goto)."""
    if ins['cmd'] == 'if':
        return [t.value for t in (ins['op1'], ins['op2']) if t.type == 'INT']
    if ins['cmd'] == 'let':
        return [t.value for t in ins['expr'] if t.type == 'INT']
    return []


# ==========================================
# 4. GERAÇÃO DE CÓDIGO INTERMEDIÁRIO (TRÊS ENDEREÇOS)
# ------------------------------------------
# Instruções (tuplas):
#   ('label', L)                    rótulo (um por linha SIMPLE: L10, L20 ...)
#   ('read', x)                     input x
#   ('write', a)                    print a
#   ('assign', x, a, op, b)         x = a op b
#   ('assign', x, a, None, None)    x = a          (cópia)
#   ('goto', L)
#   ('if', a, rel, b, L)            if a rel b goto L
#   ('halt',)
#
# Operandos: int = constante; str de 1 letra = variável SIMPLE;
#            str com 2+ caracteres = temporário (t1, t2, ...).
# ==========================================

def is_const(o):
    return isinstance(o, int)


def is_temp(o):
    return isinstance(o, str) and len(o) > 1


def line_label(n):
    return f"L{n}"


class IRGenerator:
    def __init__(self, instructions):
        self.instructions = instructions
        self.code = []
        self.temp_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    @staticmethod
    def operand_of(tok):
        return tok.value   # INT -> int, VAR -> str de 1 letra

    def generate(self):
        for ins in self.instructions:
            # Toda linha SIMPLE vira um rótulo. Uma linha 'rem' gera só o
            # rótulo, que acaba apontando para a próxima instrução emitida.
            self.code.append(('label', line_label(ins['line'])))
            cmd = ins['cmd']

            if cmd == 'input':
                self.code.append(('read', ins['var']))
            elif cmd == 'print':
                self.code.append(('write', ins['var']))
            elif cmd == 'goto':
                self.code.append(('goto', line_label(ins['dest'])))
            elif cmd == 'if':
                self.code.append(('if', self.operand_of(ins['op1']), ins['rel'],
                                  self.operand_of(ins['op2']), line_label(ins['dest'])))
            elif cmd == 'end':
                self.code.append(('halt',))
            elif cmd == 'let':
                self.gen_let(ins['var'], ins['tree'])
        return self.code

    def gen_expr(self, node):
        """Gera código para a subárvore e devolve o operando com o resultado."""
        if node[0] in ('num', 'var'):
            return node[1]
        _, op, left, right = node
        a = self.gen_expr(left)
        b = self.gen_expr(right)
        t = self.new_temp()
        self.code.append(('assign', t, a, op, b))
        return t

    def gen_let(self, var, tree):
        # A operação da raiz escreve direto na variável (evita "x = t").
        if tree[0] == 'bin':
            _, op, left, right = tree
            a = self.gen_expr(left)
            b = self.gen_expr(right)
            self.code.append(('assign', var, a, op, b))
        else:
            self.code.append(('assign', var, tree[1], None, None))


def format_ir(code):
    lines = []
    for ins in code:
        kind = ins[0]
        if kind == 'label':
            lines.append(f"{ins[1]}:")
        elif kind == 'read':
            lines.append(f"    read {ins[1]}")
        elif kind == 'write':
            lines.append(f"    write {ins[1]}")
        elif kind == 'assign':
            _, x, a, op, b = ins
            rhs = f"{a}" if op is None else f"{a} {op} {b}"
            lines.append(f"    {x} = {rhs}")
        elif kind == 'goto':
            lines.append(f"    goto {ins[1]}")
        elif kind == 'if':
            _, a, rel, b, lab = ins
            lines.append(f"    if {a} {rel} {b} goto {lab}")
        elif kind == 'halt':
            lines.append("    halt")
    return "\n".join(lines)


def ir_size(code):
    """Quantidade de instruções reais (sem contar rótulos)."""
    return sum(1 for ins in code if ins[0] != 'label')


# ==========================================
# 5. OTIMIZAÇÃO DO CÓDIGO INTERMEDIÁRIO
# ------------------------------------------
# Cada passe recebe uma lista de instruções e devolve uma nova lista.
# O otimizador repete todos os passes ativos até nada mais mudar
# (ponto fixo), pois um passe abre oportunidades para outro.
# ==========================================

def div_trunc(a, b):
    """Divisão inteira com truncamento em direção a zero (como em C/Java)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def eval_arith(a, op, b):
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    if op == '/':
        return div_trunc(a, b)
    return a - div_trunc(a, b) * b    # '%'


def eval_rel(a, rel, b):
    return {'==': a == b, '!=': a != b, '<': a < b,
            '>': a > b, '<=': a <= b, '>=': a >= b}[rel]


INVERSE_REL = {'==': '!=', '!=': '==', '<': '>=', '>=': '<', '>': '<=', '<=': '>'}


def operands_read(ins):
    """Operandos lidos por uma instrução."""
    kind = ins[0]
    if kind == 'write':
        return [ins[1]]
    if kind == 'assign':
        return [ins[2]] if ins[3] is None else [ins[2], ins[4]]
    if kind == 'if':
        return [ins[1], ins[3]]
    return []


def count_uses(code):
    uses = {}
    for ins in code:
        for o in operands_read(ins):
            if isinstance(o, str):
                uses[o] = uses.get(o, 0) + 1
    return uses


def jump_targets_of(code):
    return {ins[-1] for ins in code if ins[0] in ('goto', 'if')}


class Optimizer:
    ALL_PASSES = ['dobra_constantes', 'propagacao', 'fusao_copias', 'temporarios_mortos',
                  'desvios', 'codigo_inalcancavel', 'rotulos_inuteis']

    def __init__(self, passes=None):
        self.passes = list(self.ALL_PASSES if passes is None else passes)
        self.applied = {p: 0 for p in self.passes}

    def run(self, code):
        for _ in range(100):  # limite de segurança
            changed = False
            for name in self.passes:
                new_code = getattr(self, 'p_' + name)(code)
                if new_code != code:
                    code = new_code
                    changed = True
                    self.applied[name] += 1
            if not changed:
                break
        return code

    # ---------- dobra de constantes + simplificação algébrica ----------
    def p_dobra_constantes(self, code):
        out = []
        for ins in code:
            if ins[0] == 'assign' and ins[3] is not None:
                ins = self._simplify(ins)
            if ins[0] == 'assign' and ins[3] is None and ins[1] == ins[2]:
                continue                        # x = x  -> some
            if ins[0] == 'if' and is_const(ins[1]) and is_const(ins[3]):
                if eval_rel(ins[1], ins[2], ins[3]):
                    out.append(('goto', ins[4]))  # condição sempre verdadeira
                continue                        # sempre falsa -> some
            out.append(ins)
        return out

    @staticmethod
    def _simplify(ins):
        _, x, a, op, b = ins

        def copy(v):
            return ('assign', x, v, None, None)

        if is_const(a) and is_const(b):
            if op in '/%' and b == 0:
                return ins                      # divisão por zero: deixa para a execução
            return copy(eval_arith(a, op, b))
        if op == '+':
            if b == 0:
                return copy(a)
            if a == 0:
                return copy(b)
        elif op == '-':
            if b == 0:
                return copy(a)
            if a == b:
                return copy(0)                  # x - x = 0
        elif op == '*':
            if a == 0 or b == 0:
                return copy(0)
            if b == 1:
                return copy(a)
            if a == 1:
                return copy(b)
        elif op == '/':
            if b == 1:
                return copy(a)
        elif op == '%':
            if b == 1:
                return copy(0)
        return ins

    # ---------- propagação de constantes e de cópias (local ao bloco básico) ----------
    def p_propagacao(self, code):
        """
        Dentro de um bloco básico, se sabemos que x = 5 (ou x = y),
        trocamos os usos seguintes de x por 5 (ou y). Ao chegar em um
        rótulo, o conhecimento é descartado, pois o rótulo pode ser
        alcançado por um goto vindo de outro ponto (laços!).
        """
        out = []
        known = {}   # nome -> operando equivalente

        def sub(o):
            return known.get(o, o) if isinstance(o, str) else o

        def kill(name):
            known.pop(name, None)
            for k in [k for k, v in known.items() if v == name]:
                del known[k]

        for ins in code:
            kind = ins[0]
            if kind == 'label':
                known.clear()
                out.append(ins)
            elif kind == 'read':
                kill(ins[1])
                out.append(ins)
            elif kind == 'write':
                out.append(('write', sub(ins[1])))
            elif kind == 'if':
                out.append(('if', sub(ins[1]), ins[2], sub(ins[3]), ins[4]))
            elif kind == 'assign':
                _, x, a, op, b = ins
                a = sub(a)
                b = sub(b) if op is not None else None
                kill(x)
                if op is None and a != x:
                    known[x] = a
                out.append(('assign', x, a, op, b))
            else:
                out.append(ins)
        return out

    # ---------- fusão "t = a op b ; x = t"  ->  "x = a op b" ----------
    def p_fusao_copias(self, code):
        uses = count_uses(code)
        out = []
        i = 0
        while i < len(code):
            ins = code[i]
            if (i + 1 < len(code) and ins[0] == 'assign' and is_temp(ins[1])
                    and uses.get(ins[1], 0) == 1):
                nxt = code[i + 1]
                if nxt[0] == 'assign' and nxt[3] is None and nxt[2] == ins[1]:
                    out.append(('assign', nxt[1], ins[2], ins[3], ins[4]))
                    i += 2
                    continue
            out.append(ins)
            i += 1
        return out

    # ---------- eliminação de temporários que nunca são lidos ----------
    def p_temporarios_mortos(self, code):
        uses = count_uses(code)
        return [ins for ins in code
                if not (ins[0] == 'assign' and is_temp(ins[1]) and uses.get(ins[1], 0) == 0)]

    # ---------- otimização de desvios ----------
    def p_desvios(self, code):
        code = self._thread_jumps(code)
        code = self._invert_if_over_goto(code)
        code = self._remove_jump_to_next(code)
        return code

    @staticmethod
    def _first_real_after_label(code, label):
        """Primeira instrução (não rótulo) após o rótulo indicado."""
        for i, ins in enumerate(code):
            if ins == ('label', label):
                for j in range(i + 1, len(code)):
                    if code[j][0] != 'label':
                        return code[j]
                return None
        return None

    def _thread_jumps(self, code):
        """goto encadeado: desvio para um rótulo cuja 1ª instrução é 'goto M' vai direto para M."""
        def final_target(label):
            seen = {label}
            while True:
                first = self._first_real_after_label(code, label)
                if first is None or first[0] != 'goto' or first[1] in seen:
                    return label
                label = first[1]
                seen.add(label)

        out = []
        for ins in code:
            if ins[0] == 'goto':
                ins = ('goto', final_target(ins[1]))
            elif ins[0] == 'if':
                ins = ins[:4] + (final_target(ins[4]),)
            out.append(ins)
        return out

    @staticmethod
    def _labels_right_after(code, i):
        """Conjunto de rótulos que aparecem logo após a posição i (antes de código real)."""
        labels = set()
        j = i + 1
        while j < len(code) and code[j][0] == 'label':
            labels.add(code[j][1])
            j += 1
        return labels

    def _invert_if_over_goto(self, code):
        """
        if c goto L1        ->     if !c goto L2
        goto L2                    L1:
        L1:
        """
        out = []
        i = 0
        while i < len(code):
            ins = code[i]
            if (ins[0] == 'if' and i + 1 < len(code) and code[i + 1][0] == 'goto'
                    and ins[4] in self._labels_right_after(code, i + 1)):
                out.append(('if', ins[1], INVERSE_REL[ins[2]], ins[3], code[i + 1][1]))
                i += 2
                continue
            out.append(ins)
            i += 1
        return out

    def _remove_jump_to_next(self, code):
        """goto/if para a linha imediatamente seguinte não faz nada."""
        out = []
        for i, ins in enumerate(code):
            if ins[0] in ('goto', 'if') and ins[-1] in self._labels_right_after(code, i):
                continue
            out.append(ins)
        return out

    # ---------- eliminação de código inalcançável ----------
    def p_codigo_inalcancavel(self, code):
        """Após goto/halt, descarta tudo até o próximo rótulo que é alvo de algum desvio."""
        targets = jump_targets_of(code)
        out = []
        dead = False
        for ins in code:
            if ins[0] == 'label' and ins[1] in targets:
                dead = False
            if not dead:
                out.append(ins)
            if ins[0] in ('goto', 'halt'):
                dead = True
        return out

    # ---------- remoção de rótulos que ninguém usa ----------
    def p_rotulos_inuteis(self, code):
        """
        Um rótulo sem nenhum desvio apontando para ele não inicia bloco
        básico. Removê-lo junta blocos e amplia o alcance da propagação.
        """
        targets = jump_targets_of(code)
        return [ins for ins in code if ins[0] != 'label' or ins[1] in targets]


# ==========================================
# 6. GERAÇÃO DE CÓDIGO FINAL (SML)
# ------------------------------------------
# Etapa A: IR -> lista simbólica de instruções SML (operandos ainda por nome)
# Etapa B: peephole e alocação dos temporários
# Etapa C: montagem: endereços de memória e resolução de desvios
#          para frente com uma tabela de pendências (segunda passada)
# ==========================================

BRANCH_OPS = {'BRANCH', 'BRANCHNEG', 'BRANCHZERO'}
READS_MEMORY = {'LOAD', 'ADD', 'SUBTRACT', 'DIVIDE', 'MULTIPLY', 'MOD', 'WRITE'}
ARITH_TO_SML = {'+': 'ADD', '-': 'SUBTRACT', '*': 'MULTIPLY', '/': 'DIVIDE', '%': 'MOD'}


def data_name(o):
    """Nome simbólico de um operando na memória de dados."""
    if is_const(o):
        return f"#{o}"     # constantes: #5, #-1 ...
    return o               # variáveis (x) e temporários (t1)


def is_temp_name(name):
    return not name.startswith('#') and len(name) > 1


class SMLGenerator:
    def __init__(self, ir_code, errors, optimize=True):
        self.ir = ir_code
        self.errors = errors
        self.optimize = optimize
        self.sym = []          # ('LABEL', nome) ou (OPCODE, operando_ou_None)
        self.acc = set()       # nomes cuja posição de memória é igual ao acumulador
        self.aux_count = 0
        self.memory = None
        self.symbol_table = {}
        self.listing = []

    # ---------------- Etapa A ----------------
    def emit(self, op, operand=None):
        self.sym.append((op, operand))

    def new_aux(self, prefix):
        self.aux_count += 1
        return f"_{prefix}{self.aux_count}"

    def load(self, o):
        name = data_name(o)
        if self.optimize and name in self.acc:
            return                               # já está no acumulador
        self.emit('LOAD', name)
        self.acc = {name}

    def store(self, name):
        if self.optimize and name in self.acc:
            return                               # memória já tem esse valor
        self.emit('STORE', name)
        self.acc.add(name)

    def gen_assign(self, x, a, op, b):
        if op is None:
            self.load(a)
            self.store(x)
            return

        if op == '%' and 'MOD' not in SML_OPCODES:
            # a % b  =  a - (a / b) * b
            aux = self.new_aux('r')
            self.load(a)
            self.emit('DIVIDE', data_name(b))
            self.emit('MULTIPLY', data_name(b))
            self.acc = set()
            self.store(aux)
            self.load(a)
            self.emit('SUBTRACT', aux)
            self.acc = set()
            self.store(x)
            return

        # operação comutativa: se o 2º operando já está no acumulador, troca a ordem
        if (self.optimize and op in '+*' and data_name(b) in self.acc
                and data_name(a) not in self.acc):
            a, b = b, a
        self.load(a)
        self.emit(ARITH_TO_SML[op], data_name(b))
        self.acc = set()
        self.store(x)

    def gen_if(self, a, rel, b, label):
        # a < b   <=>  a - b < 0       a > b   <=>  b - a < 0
        if rel in ('>', '>='):
            first, second = b, a
        else:
            first, second = a, b
        if (self.optimize and rel in ('==', '!=') and data_name(second) in self.acc
                and data_name(first) not in self.acc):
            first, second = second, first        # igualdade é simétrica

        self.load(first)
        if not (self.optimize and second == 0):  # "x - 0" é desnecessário
            self.emit('SUBTRACT', data_name(second))
            self.acc = set()

        if rel == '==':
            self.emit('BRANCHZERO', label)
        elif rel == '!=':
            skip = self.new_aux('s')
            self.emit('BRANCHZERO', skip)
            self.emit('BRANCH', label)
            self.sym.append(('LABEL', skip))
            self.acc = set()
        elif rel in ('<', '>'):
            self.emit('BRANCHNEG', label)
        else:   # '<=' ou '>='
            self.emit('BRANCHNEG', label)
            self.emit('BRANCHZERO', label)

    def translate(self):
        for ins in self.ir:
            kind = ins[0]
            if kind == 'label':
                self.sym.append(('LABEL', ins[1]))
                self.acc = set()                 # pode-se chegar aqui por desvio
            elif kind == 'read':
                self.emit('READ', ins[1])
                self.acc.discard(ins[1])         # a variável mudou de valor
            elif kind == 'write':
                self.emit('WRITE', data_name(ins[1]))
            elif kind == 'assign':
                self.gen_assign(*ins[1:])
            elif kind == 'goto':
                self.emit('BRANCH', ins[1])
            elif kind == 'if':
                self.gen_if(*ins[1:])
            elif kind == 'halt':
                self.emit('HALT')

    # ---------------- Etapa B ----------------
    def remove_dead_temp_stores(self):
        """Peephole: STORE em temporário que nunca é lido depois é removido."""
        read_names = {operand for op, operand in self.sym if op in READS_MEMORY}
        self.sym = [(op, operand) for op, operand in self.sym
                    if not (op == 'STORE' and is_temp_name(operand) and operand not in read_names)]

    def allocate_temps(self):
        """
        Temporários com tempos de vida que não se sobrepõem compartilham a
        mesma posição de memória (alocação por varredura linear). Como os
        temporários vivem dentro de um bloco básico, a ordem linear basta.
        """
        first, last = {}, {}
        for i, (op, operand) in enumerate(self.sym):
            if op != 'LABEL' and op not in BRANCH_OPS and operand and is_temp_name(operand):
                first.setdefault(operand, i)
                last[operand] = i

        slot_of = {}
        slot_free_at = []          # slot_free_at[k] = índice da última leitura do slot k
        for name in sorted(first, key=lambda n: first[n]):
            for k, end in enumerate(slot_free_at):
                if end < first[name]:
                    slot_of[name] = k
                    slot_free_at[k] = last[name]
                    break
            else:
                slot_of[name] = len(slot_free_at)
                slot_free_at.append(last[name])

        self.sym = [(op, f"_T{slot_of[operand]}" if (op != 'LABEL' and op not in BRANCH_OPS
                                                     and operand in slot_of) else operand)
                    for op, operand in self.sym]

    # ---------------- Etapa C ----------------
    def assemble(self):
        n_instr = sum(1 for op, _ in self.sym if op != 'LABEL')
        data_names = []
        for op, operand in self.sym:
            if op != 'LABEL' and op not in BRANCH_OPS and operand is not None:
                if operand not in data_names:
                    data_names.append(operand)

        # constantes geradas pela otimização (ex.: 0 - 1 = -1) também precisam caber
        for name in data_names:
            if name.startswith('#') and abs(int(name[1:])) > SML_WORD_MAX:
                self.errors.add(None, None, 'Síntese',
                                f"constante {name[1:]} (resultado de expressão constante) "
                                f"excede o limite da palavra do Simpletron ({SML_WORD_MAX}).")

        if n_instr + len(data_names) > SML_MEM_SIZE:
            self.errors.add(None, None, 'Síntese',
                            f"o programa não cabe na memória do Simpletron: "
                            f"{n_instr} instruções + {len(data_names)} dados = "
                            f"{n_instr + len(data_names)} palavras (máximo {SML_MEM_SIZE}).")
        if self.errors.has_errors():
            return False

        memory = [0] * SML_MEM_SIZE
        labels = {}          # rótulo -> endereço
        pending = []         # tabela de pendências: (endereço_da_instrução, rótulo)
        data_addr = {}
        # dados logo após a última instrução, ou a partir do fim da memória
        next_data = n_instr if SML_DATA_AFTER_CODE else SML_MEM_SIZE - 1
        data_step = 1 if SML_DATA_AFTER_CODE else -1
        ic = 0                         # instruções crescem a partir de 00

        for op, operand in self.sym:
            if op == 'LABEL':
                labels[operand] = ic
                continue

            if operand is None:
                addr = 0
            elif op in BRANCH_OPS:
                if operand in labels:
                    addr = labels[operand]            # desvio para trás: já conhecido
                else:
                    addr = 0
                    pending.append((ic, operand))     # desvio para frente: resolve depois
            else:
                if operand not in data_addr:
                    data_addr[operand] = next_data
                    memory[next_data] = int(operand[1:]) if operand.startswith('#') else 0
                    next_data += data_step
                addr = data_addr[operand]

            memory[ic] = SML_OPCODES[op] * SML_MEM_SIZE + addr
            self.listing.append((ic, op, operand))
            ic += 1

        # segunda passada: completa os desvios para frente
        for at, label in pending:
            memory[at] += labels[label]

        self.memory = memory
        self.symbol_table = data_addr
        self.labels = labels
        return True

    def generate(self):
        self.translate()
        if self.optimize:
            self.remove_dead_temp_stores()
        self.allocate_temps()
        return self.assemble()

    # ---------------- saída ----------------
    @staticmethod
    def format_word(value):
        digits = SML_OPCODE_DIGITS + SML_ADDR_DIGITS
        if value < 0:
            return f"-{abs(value):0{digits}d}"
        return f"{'+' if SML_OUTPUT_PLUS_SIGN else ''}{value:0{digits}d}"

    def write_file(self, path):
        words = self.memory
        if SML_OUTPUT_ONLY_USED and SML_DATA_AFTER_CODE:
            words = self.memory[:self.word_count()]
        with open(path, 'w', encoding='utf-8') as f:
            for value in words:
                f.write(self.format_word(value) + "\n")
            if SML_OUTPUT_SENTINEL is not None:
                f.write(f"{SML_OUTPUT_SENTINEL}\n")

    def word_count(self):
        return len(self.listing) + len(self.symbol_table)

    def print_listing(self):
        addr_to_labels = {}
        for lab, addr in self.labels.items():
            if not lab.startswith('_'):
                addr_to_labels.setdefault(addr, []).append(lab)

        print("   end   palavra   instrução           rótulo(s)")
        for ic, op, operand in self.listing:
            arg = '' if operand is None else operand
            labs = ' '.join(sorted(addr_to_labels.get(ic, []), key=lambda s: int(s[1:])))
            print(f"   {ic:02d}    {self.format_word(self.memory[ic])}     "
                  f"{op:<10} {arg:<8} {labs}")
        print("   --    -----     -----")
        for name, addr in sorted(self.symbol_table.items(), key=lambda kv: kv[1] if SML_DATA_AFTER_CODE else -kv[1]):
            kind = ('constante' if name.startswith('#')
                    else 'temporário' if name.startswith('_') else 'variável')
            print(f"   {addr:02d}    {self.format_word(self.memory[addr])}     "
                  f"{kind:<10} {name}")


# ==========================================
# 7. DUMP DE TOKENS NO FORMATO OFICIAL DA DISCIPLINA
#    [código, valor, (linha, coluna)]
# ==========================================

_KEYWORD_CODES = {'rem': 61, 'input': 62, 'let': 63, 'print': 64,
                  'goto': 65, 'if': 66, 'end': 67}
_ARITHOP_CODES = {'+': 21, '-': 22, '*': 23, '/': 24, '%': 25}
_RELOP_CODES = {'==': 31, '!=': 32, '>': 33, '<': 34, '>=': 35, '<=': 36}


def token_code(tok):
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
    literal_table = {}
    literal_order = []

    def literal_index(value):
        key = str(value)
        if key not in literal_table:
            literal_table[key] = len(literal_order)
            literal_order.append(key)
        return literal_table[key]

    lines = [l for l in raw_code.splitlines() if l.strip()]
    dummy_errors = ErrorCollector()

    for i, raw_line in enumerate(lines):
        phys_idx = i + 1
        tokens = tokenize_line(raw_line, phys_idx, dummy_errors)

        parts = []
        for tok in tokens:
            code = token_code(tok)
            value_field = literal_index(tok.value) if tok.type in ('INT', 'VAR') else ''
            parts.append(f"[{code}, {value_field}, ({tok.line_num}, {tok.col})]")

        is_last_line = (i == len(lines) - 1)
        end_code = 3 if is_last_line else 10
        end_col = len(raw_line.rstrip()) + 1
        parts.append(f"[{end_code}, , ({phys_idx}, {end_col})]")
        print(''.join(parts))

    print("\nTabela de constantes/identificadores:")
    for idx, lex in enumerate(literal_order):
        print(f"{idx} : {lex}")


# ==========================================
# 8. DRIVER DO COMPILADOR
# ==========================================

# Nomes que o professor pediu: ele coloca o programa SIMPLE no source.txt,
# aperta RUN e o compilador tem que gerar o binary.txt na mesma pasta.
ARQUIVO_FONTE = 'source.txt'
ARQUIVO_BINARIO = 'binary.txt'


def default_output_name(filepath):
    return os.path.splitext(filepath)[0] + '.sml'


def compile_source(code, optimize=True):
    """
    Executa todas as fases sobre o texto-fonte.
    Devolve (errors, parser, ir_original, ir_final, generator).
    Usado pelo driver e pelos testes.
    """
    errors = ErrorCollector()
    parser = Parser(code, errors)
    parser.parse()
    SemanticAnalyzer(parser, errors).analyze()
    if errors.has_errors():
        return errors, parser, None, None, None

    ir_original = IRGenerator(parser.instructions).generate()
    ir_final = Optimizer().run(ir_original) if optimize else ir_original

    generator = SMLGenerator(ir_final, errors, optimize=optimize)
    generator.generate()
    return errors, parser, ir_original, ir_final, generator


def compile_file(filepath, output=None, show_ir=False, show_asm=False, optimize=True):
    filename = os.path.basename(filepath)
    print("=" * 60)
    print(f"COMPILANDO ARQUIVO: {filename}")
    print("=" * 60)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except OSError as err:
        print(f">> ERRO AO ABRIR ARQUIVO: {err}\n")
        return False

    errors, parser, ir_original, ir_final, generator = compile_source(code, optimize)

    if ir_original is None:
        errors.report()
        print("   Síntese não executada: corrija os erroscima.\n")
        return False

    if show_ir:
        print("\n--- Código intermediário (três endereços) ---")
        print(format_ir(ir_original))
        if optimize:
            print(f"\n--- Código intermediário otimizado ---")
            print(format_ir(ir_final))
            print(f"\n   instruções: {ir_size(ir_original)} -> {ir_size(ir_final)}")
        print()

    if errors.has_errors():
        errors.report()
        print()
        return False

    output = output or default_output_epath)
    generator.write_file(output)

    if show_asm:
        print("--- Código SML ---")
        generator.print_listing()
        print()
    else:
        # Mostra também no console o que foi gravado no arquivo, assim dá pra
        # conferir (ou copiar) o código objeto direto na tela do onlineGDB.
        print(f"--- Conteúdo de {os.path.basename(output)} ---")
        with open(output, 'r', encoding='utf-8') as f:
            print(f.read().rstrip())
        print()

    print(">> STATUS: SUC)
    print("   Análise léxica, sintática e semântica OK.")
    print(f"   Otimização: {'ligada' if optimize else 'desligada'}")
    print(f"   Memória usada: {len(generator.listing)} instruções + "
          f"{len(generator.symbol_table)} dados = {generator.word_count()} de {SML_MEM_SIZE} palavras")
    print(f"   Código objeto gravado em: {output}\n")
    return True


def print_usage():
    print(__doc__)


# Nosso mascote! O compilador chama Bidu, então nada mais justo que um
# cachorrinho aa vez que alguém aperta o RUN.
# (raw string pra não ter que escapar as barras do desenho)
BIDU = r"""
        / \__
       (    @\___       Au au! Compilador Bidu
       /         O      SIMPLE  ->  Simpletron (SML)
      /   (_____/       Caio Silveira & Mayron Malaquias
     /_____/   U
"""


def print_banner():
    print(BIDU)


if __name__ == '__main__':
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print_usage()
        sys.exit(0)

    output = None
    if '-o' in args:
      k = args.index('-o')
        if k + 1 >= len(args):
            print("Erro: '-o' precisa do nome do arquivo de saída.")
            sys.exit(1)
        output = args[k + 1]
        del args[k:k + 2]

    flags = {a for a in args if a.startswith('--')}
    files = [a for a in args if not a.startswith('--')]
    unknown = flags - {'--tokens', '--ir', '--asm', '--no-opt'}
    if unknown:
        print(f"Opção desconhecida: {', '.join(sorted(unknown))}")
        print_usage()
        sys.exit(1)

    omize = '--no-opt' not in flags

    # No --tokens o cachorro fica quieto, pra saída sair limpa no formato da disciplina
    if '--tokens' not in flags:
        print_banner()

    if '--tokens' in flags:
        if not files:
            print("Informe um arquivo: python compilador_simple.py arquivo.simple --tokens")
        else:
            with open(files[0], 'r', encoding='utf-8') as f:
                dump_tokens(f.read())
    elif files:
        if output and len(files) > 1:
            print("Erro: -o' só pode ser usado com um único arquivo.")
            sys.exit(1)
        ok = True
        for path in files:
            ok = compile_file(path, output, '--ir' in flags, '--asm' in flags, optimize) and ok
        sys.exit(0 if ok else 1)
    else:
        # Sem nenhum arquivo na linha de comando = botão RUN do onlineGDB.
        # Procuramos o source.txt na pasta do próprio .py (e não só na pasta
        # atual), pra funcionar mesmo se rodarem o script de outro lugar.
        pasta = os.path.dios.path.abspath(__file__))
        fonte = os.path.join(pasta, ARQUIVO_FONTE)
        if not os.path.exists(fonte) and os.path.exists(ARQUIVO_FONTE):
            pasta, fonte = '.', ARQUIVO_FONTE
        if not os.path.exists(fonte):
            print(f"Arquivo '{ARQUIVO_FONTE}' não encontrado. Crie o {ARQUIVO_FONTE} com o "
                  f"programa SIMPLE na mesma pasta do compilador e execute de novo.")
            sys.exit(1)
        binario = output or os.path.join(pasta, ARQUIVO_BINARIO)
        o = compile_file(fonte, binario, '--ir' in flags, '--asm' in flags, optimize)
        sys.exit(0 if ok else 1)
