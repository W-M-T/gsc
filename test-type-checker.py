#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Int a = 2;  
        Bool b = True;
        Char c = d;
        
        f(x, y) :: Int Int -> Int {
            Int b = a * 2;
            Int x = 2 + b;
            
            return b * (x + y);
        }
    ''')

    # Tokenize / parse
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)
    ast = SPL.parse_strict(tokenlist, testprog)

    # Build symbol table
    ERROR_HANDLER.setSourceMapping(testprog, [])
    symbol_table = buildSymbolTable(ast)
    print(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Normalize table
    normalizeAllTypes(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Resolve Expr names
    resolveNames(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Parse expression
    #op_table = buildOperatorTable(symbol_table)
    #decorated_ast = fixExpression(ast, op_table)
    #ERROR_HANDLER.checkpoint()

    # Type check
    #typecheck_globals(decorated_ast, symbol_table, op_table)
    #typecheck_func(ast.decls[0].val, symbol_table, op_table)
    #ERROR_HANDLER.checkpoint()

if __name__ == "__main__":
    main()