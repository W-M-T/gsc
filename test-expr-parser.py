#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
    
    Int pi = 3;
    Int t = pi * (4 + 2) * 3;
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    x = SPL.parse_strict(tokenlist, testprog)

    symbol_table = buildSymbolTable(x)

    print(x.decls[1].val.expr)

    print(parseExpression(symbol_table, x.decls[1].val.expr.contents, 1))
    #print(x.tree_string())

if __name__ == "__main__":
    main()