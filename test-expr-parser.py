#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Bool a = ~(f(a * 2, 5 * 8) && true);
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    parse_res = SPL.parse_strict(tokenlist, testprog)

    symbol_table = buildSymbolTable(parse_res)
    op_table = buildOperatorTable(symbol_table)

    print("Initial")
    print(parse_res)
    result = treemap(parse_res, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: fixExpression(y, op_table)))
    print("After")
    print(result)

if __name__ == "__main__":
    main()