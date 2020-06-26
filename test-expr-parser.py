#!/usr/bin/env python3

from lib.parser.parser import *
from lib.parser.lexer import tokenize
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Bool a = ~(f(b * 2, 5 * 8) && True);
    ''')

    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)
    ast = SPL.parse_strict(tokenlist, testprog)

    # Build symbol table
    ERROR_HANDLER.setSourceMapping(testprog, [])
    symbol_table = buildSymbolTable(ast)
    ERROR_HANDLER.checkpoint()

    # Normalize table
    normalizeAllTypes(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Resolve Expr names
    resolveNames(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Parse expression
    op_table = buildOperatorTable()

    fixExpression(ast, op_table)
    ERROR_HANDLER.checkpoint()

if __name__ == "__main__":
    main()