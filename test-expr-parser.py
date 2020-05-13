#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Int pi = 2 + 3;
        Int a = 5 *4 ** 2;
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    x = SPL.parse_strict(tokenlist, testprog)

    #symbol_table = buildSymbolTable(x)
    symbol_table = []

    #print(fixExpression(x.decls[2].val.expr.contents, symbol_table))

    result = treemap(x, selectiveApply, {'f': fixExpression,'type': AST.DEFERREDEXPR})
    print(result)

if __name__ == "__main__":
    main()