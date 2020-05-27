#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''  
        Int a = 5;
        (Int, Int) pos = (2, 3);
    ''')

    # Tokenize / parse
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)
    parse_res = SPL.parse_strict(tokenlist, testprog)

    # Build symbol table
    ERROR_HANDLER.setSourceMapping(testprog, [])
    symbol_table = buildSymbolTable(parse_res)
    ERROR_HANDLER.checkpoint()

    # Parse expression
    op_table = buildOperatorTable(symbol_table)
    ast = fixExpression(parse_res, op_table)
    ERROR_HANDLER.checkpoint()

    # Check for dead code
    typecheck_globals(ast, symbol_table)
    ERROR_HANDLER.checkpoint()

if __name__ == "__main__":
    main()