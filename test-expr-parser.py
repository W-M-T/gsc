#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        infixl 7 ** (a, b) :: Int Int -> Int {
            Int result = a;
            Int a = 2;
            while(result > b) {
                result = result - b;
            }
            return result;
        }
        Int pi = 2 + 3;
        Int a = 5 * 4 ** 2;
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    x = SPL.parse_strict(tokenlist, testprog)

    symbol_table = buildSymbolTable(x)
    op_table = BUILTIN_INFIX_OPS

    for x in symbol_table.functions:
        f = symbol_table.functions[x]
        if x[0] is FunUniq.INFIX:
            precedence = 'L' if f[0]['def'].kind == FunKind.INFIXL else 'R'
            op_table[x[1]] = ("T T -> T", f[0]['def'].fixity, precedence)

    result = treemap(x, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: fixExpression(y, op_table)))
    print(result)

if __name__ == "__main__":
    main()