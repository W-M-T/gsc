#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Bool a = 3 * -((2 + 3) * 5);
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    parse_res = SPL.parse_strict(tokenlist, testprog)

    symbol_table = buildSymbolTable(parse_res)
    op_table = BUILTIN_INFIX_OPS

    for x in symbol_table.functions:
        f = symbol_table.functions[x]
        if x[0] is FunUniq.INFIX:
            precedence = 'L' if f[0]['def'].kind == FunKind.INFIXL else 'R'
            op_table[x[1]] = ("T T -> T", f[0]['def'].fixity.val, precedence)

    print("Initial")
    print(parse_res)
    result = treemap(parse_res, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: fixExpression(y, op_table)))
    print("After")
    print(result)

if __name__ == "__main__":
    main()