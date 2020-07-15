#!/usr/bin/env python3

from lib.parser.lexer import tokenize
from lib.parser.parser import *
from semantic_analysis import *
from lib.analysis.typechecker import *
from lib.builtins.builtin_mod import generateBuiltinOps, mergeCustomOps, generateBuiltinFuncs
from lib.codegen.codegen import generate_object_file
from lib.datastructure.symbol_table import ExternalTable
import os

from lib.imports.imports import SOURCE_EXT
def main():
    from argparse import ArgumentParser
    from lib.parser.lexer import tokenize
    argparser = ArgumentParser(description="TESTCODEGEN")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default=None)
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import libraries from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated library_name:path mapping list, to explicitly specify import paths", type=str)
    args = argparser.parse_args()

    if not args.infile is None:
        if not args.infile.endswith(SOURCE_EXT):
            print("Input file needs to be {}".format(SOURCE_EXT))
            exit()
        else:
            infile = open(args.infile, "r")
            tokenstream = tokenize(infile)
            ast = parseTokenStream(tokenstream, infile)

            ERROR_HANDLER.setSourceMapping(infile)

        import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
        if not (all(map(lambda x: len(x) == 2, import_mapping)) and all(
                map(lambda x: all(map(lambda y: len(y) > 0, x)), import_mapping))):
            print("Invalid import mapping")
            exit()
        # print(import_mapping)
        import_mapping = {a: os.path.splitext(b)[0] for (a, b) in import_mapping}

        main_mod_path = os.path.splitext(args.infile)[0]
        module_name = os.path.basename(main_mod_path)

    else:
        from io import StringIO

        module_name = "tuples"
        testprog = StringIO(''' 
            
        ''')

        # Tokenize / parse
        tokenstream = tokenize(testprog)

        tokenlist = list(tokenstream)
        ast = SPL.parse_strict(tokenlist, testprog)

        ERROR_HANDLER.setSourceMapping(testprog)

        module_name = "testing"

    # Build symbol table
    symbol_table = buildSymbolTable(ast)
    ERROR_HANDLER.checkpoint()

    # Build external table
    headerfiles = getImportFiles(ast, HEADER_EXT, os.path.dirname(args.infile),
                                 file_mapping_arg=import_mapping,
                                 lib_dir_path=args.lp,
                                 lib_dir_env=os.environ[
                                     IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
    # Get all external symbols
    external_table, dependencies = getExternalSymbols(ast, headerfiles)
    external_table = enrichExternalTable(external_table)
    print(external_table)
    ERROR_HANDLER.checkpoint()

    # Normalize table
    # normalizeAllTypes(symbol_table, external_table)
    # ERROR_HANDLER.checkpoint()

    # Resolve Expr names
    resolveNames(symbol_table)
    ERROR_HANDLER.checkpoint()

    # Parse expressions
    fixExpression(ast, symbol_table, external_table)
    ERROR_HANDLER.checkpoint()

    # Function control flow analysis
    analyseFunc(symbol_table)
    ERROR_HANDLER.checkpoint()

    print(ast)
    # Typechecking
    typecheck_globals(symbol_table, external_table)
    typecheck_functions(symbol_table, external_table)
    ERROR_HANDLER.checkpoint()

    # Code gen
    gen_code = generate_object_file(symbol_table, module_name, dependencies)
    #print(gen_code)

    with open('example programs/imports_overloading/' + module_name + '.splo', 'w+') as fh:
        fh.write(gen_code)

if __name__ == "__main__":
    main()