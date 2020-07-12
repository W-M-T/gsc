#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *
from lib.builtins.builtin_mod import generateBuiltinOps, mergeCustomOps, generateBuiltinFuncs
from lib.codegen.codegen import generate_object_file
from lib.datastructure.symbol_table import ExternalTable

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

        module_name = "return-test"
        testprog = StringIO('''
            type Coord = (Int, Int)
        
            main() :: -> Int {
                Coord x = (2, 2);
                Int i = 5;
                
                while(i > 5) {
                    break;
                }   
                
                 while(i > 5) {
                    break;
                }   
                
                i = 3;
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

    # Build external table
    external_table = enrichExternalTable(ExternalTable())

    # Parse expressions
    fixExpression(ast, external_table)
    ERROR_HANDLER.checkpoint()

    # Type check
    analyseFunc(ast)
    ERROR_HANDLER.checkpoint()

    #typecheck_globals(symbol_table, external_table)
    #typecheck_functions(symbol_table, external_table)
    #ERROR_HANDLER.checkpoint()

    #gen_code = generate_object_file(symbol_table, module_name)
    #print(gen_code)

    #with open('generated/' + module_name + '.splo', 'w+') as fh:
    #    fh.write(gen_code)

if __name__ == "__main__":
    main()