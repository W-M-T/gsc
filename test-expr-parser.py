#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        infixr 10 ** (a, b) :: Int Int -> Int {
            Int result = a;
            Int a = 2;
            while(result > b) {
                result = result - b;
            }
            return result;
        }
        Int pi = f(2 + 3, 4 * 5);
        Int t = pi ** 5 ** 3 + 2;
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    x = SPL.parse_strict(tokenlist, testprog)

    symbol_table = buildSymbolTable(x)

    print("Expression:")
    print(x.decls[1].val.expr.tree_string())

    #print(fixExpression(x.decls[1].val.expr.contents, symbol_table))
    #print(x.tree_string())

if __name__ == "__main__":
    main()