#!/usr/bin/env python3

from lib.parser.lexer import tokenize
import os
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *
from lib.codegen.codegen import generate_object_file

from lib.imports.imports import SOURCE_EXT
def main():
    from argparse import ArgumentParser
    from lib.parser.lexer import tokenize
    argparser = ArgumentParser(description="TESTCODEGEN")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default=None)
    args = argparser.parse_args()

    if not args.infile is None:
        if not args.infile.endswith(SOURCE_EXT):
            print("Input file needs to be {}".format(SOURCE_EXT))
            exit()
        else:
            infile = open(args.infile, "r")
            tokenstream = tokenize(infile)
            ast = parseTokenStream(tokenstream, infile)

            ERROR_HANDLER.setSourceMapping(infile, [])

    else:
        from io import StringIO

        module_name = "control-stmt"
        testprog = StringIO('''
            main() :: -> Int {
               Int a = 5;
               if (a >= 2) {
                return 3;
               }
               else {
                return 4;
               }
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

    gen_code = generate_object_file(symbol_table, module_name)
    print(gen_code)

    with open('generated/' + module_name + '.splo', 'w+') as fh:
        fh.write(gen_code)

if __name__ == "__main__":
    main()