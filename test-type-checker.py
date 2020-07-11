#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *

def main():
    from io import StringIO

    module_name = "test"
    testprog = StringIO('''
    
        Bool x = -5;
    
        prefix - (x) :: Int -> Bool {
            return True;
        }
        
        prefix ! (x) :: Int -> Bool {
            return False;
        }
    
        /*infixl 7 ++ (a, b) :: Int Int -> Int {
            return a + b + 2;
        }*/
    
        main() :: -> Int {
            Bool x = !(-(5));
            
            x = True;
        }

    ''')

    # Tokenize / parse
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)
    ast = SPL.parse_strict(tokenlist, testprog)

    # Build symbol table
    ERROR_HANDLER.setSourceMapping(testprog)
    symbol_table = buildSymbolTable(ast)
    ERROR_HANDLER.checkpoint()

    # Normalize table
    normalizeAllTypes(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Resolve Expr names
    resolveNames(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Build operator table
    op_table = buildOperatorTable()
    mergeCustomOps(op_table, symbol_table, module_name)
    builtin_funcs = generateBuiltinFuncs()

    # Parse expressions
    fixExpression(ast, op_table)
    ERROR_HANDLER.checkpoint()

    # Type check
    typecheck_globals(symbol_table, op_table)
    typecheck_functions(symbol_table, op_table, builtin_funcs)
    ERROR_HANDLER.checkpoint()

if __name__ == "__main__":
    main()