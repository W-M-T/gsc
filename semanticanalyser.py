#!/usr/bin/env python3

from collections import namedtuple
from AST import *
from util import TOKEN

OPDATA = namedtuple('OPDATA', 'fixity precedence')

# Source: doc/operator_precedence.md
# Operators without precendence are defined to be left associative.
OPTABLE = {
    '||':   OPDATA(2, 'right'),
    '&&':   OPDATA(3, 'right'),
    '==':   OPDATA(4, 'left'),
    '!=':   OPDATA(4, 'left'),
    '<':    OPDATA(4, 'left'),
    '<=':   OPDATA(4, 'left'),
    '>=':   OPDATA(4, 'left'),
    '>':    OPDATA(4, 'left'),
    ':':    OPDATA(5, 'right'),
    '+':    OPDATA(6, 'left'),
    '-':    OPDATA(6, 'left'),
    '*':    OPDATA(7, 'left'),
    '/':    OPDATA(7, 'left')
}

# Add customly defined operators to the operator table
def complement_operator_table(ast):
    custom_ops = {}
    for decl in ast.decls:
        if type(decl.val) == AST.FUNDECL and (decl.val.kind == FunKind.INFIXL or decl.val.kind == FunKind.INFIXR):
            op = decl.val
            precedence = "right" if op.kind == FunKind.INFIXR else "left"
            if op.id.val in OPTABLE:
                print("ERROR: Cannot define operator '" + op.id.val + "', as it is not possible to redefine an predefined operator.")
            elif op.id.val in custom_ops and (custom_ops[op.id.val].fixity is not op.fixity.val or custom_ops[op.id.val].precedence is not precedence):
                print("ERROR: Operator '" + op.id.val + "' was defined multiply times with varying fixity or precedence.")
            else:
                custom_ops[op.id.val] = OPDATA(op.fixity.val, precedence)

    # Beautify this?
    for k in custom_ops.keys():
        OPTABLE[k] = custom_ops[k]

# Parse expressions by performing precedence climbing algorithm.
# TODO: Determine what we return here, do our ParsedExpr nodes contain a subtree?
def parse_expressions(ast):
    pass

# Perform all of the semantic analysis sequentially.
# TODO: Figure our if we can interleave certain operations.
def analyse(ast):
    complement_operator_table(ast)

    parse_expressions(ast)

if __name__ == "__main__":
    from io import StringIO
    from lexer import tokenize
    from parser import SPL

    testprog = StringIO('''
infixl 7 % (a, b) :: Int Int -> Int {
    Int result = a;
    while(result > b) {
        result = result - b;
    }
    return result;
}

fab (p, q) :: Int Int -> Int {
    Int n = 0;
    n = p % q;
}
''')

    tokens = list(tokenize(testprog))
    print(tokens)
    x = SPL.parse_strict(tokens, testprog)
    print("PARSED X =============================")
    print(x.tree_string())

    analyse(x)

    print("DONE")
