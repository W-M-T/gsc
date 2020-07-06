#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *
from lib.codegen.codegen import generate_code

def main():
    from io import StringIO

    testprog = StringIO('''    
        Int a = 5;
        Int b = 3;
        
        main() :: -> Bool {
            Int c = d;
            
            if(c > b) {
                return True;
            }
            else {
                return False;
            }
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

    # Build operator table
    op_table = buildOperatorTable()
    mergeCustomOps(op_table, symbol_table)

    # Parse expressions
    fixExpression(ast, op_table)
    ERROR_HANDLER.checkpoint()

    # Type check
    typecheck_globals(symbol_table, op_table)
    typecheck_functions(symbol_table, op_table)
    ERROR_HANDLER.checkpoint()


    generate_code(symbol_table, "main")

if __name__ == "__main__":
    main()