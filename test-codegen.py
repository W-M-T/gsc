#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *
from lib.codegen.codegen import generate_object_file

def main():
    from io import StringIO

    testprog = StringIO('''
        Int b  = 5;
    
        main() :: -> Int {
            Int value = read();
        
            print(value);
            
            return 5;
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
    builtin_funcs = generateBuiltinFuncs()

    # Parse expressions
    fixExpression(ast, op_table)
    ERROR_HANDLER.checkpoint()

    # Type check
    typecheck_globals(symbol_table, op_table)
    typecheck_functions(symbol_table, op_table, builtin_funcs)
    ERROR_HANDLER.checkpoint()

    for f in symbol_table.functions:
        for of in symbol_table.functions[f]:
            print(of['def'].type)

    generate_object_file(symbol_table, "test")

if __name__ == "__main__":
    main()