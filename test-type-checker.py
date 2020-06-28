#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *

def main():
    from io import StringIO

    testprog = StringIO('''
        Int a = 2;  
        Bool b = True;
        
        /*g(a, b) :: Int Int -> Int {
            return a > b;
        }*/
        
        g(x, y) :: (Bool, (Int, Int)) Int -> Bool {
            return x > 0;
        }
        
        h(x) :: Int -> Bool {
            return True;
        }
        
        h(x) :: Int -> Int {
            return 5;
        }
        
        f(x, y) :: Int Int -> Int {
            Bool a = True;

            h(1);
            
            return a;
        }
    ''')

    # Tokenize / parse
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

    # Type check
    typecheck_globals(symbol_table, op_table)
    typecheck_functions(symbol_table, op_table)
    ERROR_HANDLER.checkpoint()

if __name__ == "__main__":
    main()