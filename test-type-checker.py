#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *

def main():
    from io import StringIO

    testprog = StringIO('''
        main() :: -> Int {
            //(Int, (Int, Int)) a = (2, (3, 7));
            [Int] b = 2 : [];
            
            //a.fst.snd = 5;
            b.fst = 7;
        
            return 0;
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