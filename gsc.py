#!/usr/bin/env python3

import os
from argparse import ArgumentParser

from gsl import linkObjectFiles, write_out, make_import_mapping
from lib.analysis.error_handler import *

from lib.parser.lexer import tokenize, REG_FIL
from lib.parser.parser import parseTokenStream

# TODO do not import all of this but just use analyse instead or something
from semantic_analysis import buildSymbolTable, forbid_illegal_types, fixate_operator_properties, check_functype_clashes, normalizeAllTypes, resolveNames, analyseFunc, fixExpression
from lib.analysis.typechecker import typecheck_globals, typecheck_functions
from lib.builtins.builtin_mod import enrichExternalTable
from lib.codegen.codegen import generate_object_file
from lib.imports.imports import export_headers, getHeaders, getExternalSymbols, HEADER_EXT
from lib.imports.imports import validate_modname, get_type_dependencies, IMPORT_DIR_ENV_VAR_NAME, SOURCE_EXT, \
    OBJECT_EXT, TARGET_EXT
from lib.imports.objectfile_imports import getObjectFiles
from lib.parser.lexer import tokenize
from lib.parser.parser import parseTokenStream



def generateObjectFile(ast, args, main_mod_name, import_mapping):
    headerfiles, typesyn_headerfiles = getHeaders(ast,
        main_mod_name,
        HEADER_EXT,
        os.path.dirname(args.infile),
        file_mapping_arg=import_mapping,
        lib_dir_path=args.lp,
        lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)

    ext_table, dependency_names = getExternalSymbols(ast, main_mod_name, headerfiles, typesyn_headerfiles)
    ext_table = enrichExternalTable(ext_table)
    ERROR_HANDLER.checkpoint()

    symbol_table, ext_table = buildSymbolTable(ast, main_mod_name, just_for_headerfile=False, ext_symbol_table=ext_table)

    normalizeAllTypes(ast, symbol_table, ext_table, main_mod_name, full_normalize=True, headerfiles=headerfiles, typesyn_headerfiles=typesyn_headerfiles)
    #exit()
    fixate_operator_properties(symbol_table, ext_table)
    check_functype_clashes(symbol_table, ext_table)
    #exit()

    forbid_illegal_types(symbol_table, ext_table)

    #print(symbol_table)
    #print(ext_table)
    #

    # Resolve Expr names
    resolveNames(symbol_table, ext_table)
    ERROR_HANDLER.checkpoint()

    # Parse expressions
    fixExpression(ast, symbol_table, ext_table)
    ERROR_HANDLER.checkpoint()

    # Function control flow analysis
    analyseFunc(symbol_table)
    ERROR_HANDLER.checkpoint()

    typecheck_globals(symbol_table, ext_table)
    typecheck_functions(symbol_table, ext_table)
    ERROR_HANDLER.checkpoint()

    gen_code = generate_object_file(symbol_table, ext_table, headerfiles, main_mod_name, dependency_names)

    return gen_code



def main():
    argparser = ArgumentParser(description="SPL Compiler")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import header files from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated object_file:path mapping list, to explicitly specify import header paths", type=str)
    argparser.add_argument("-o", metavar="OUTPUT", help="Output file")
    argparser.add_argument("-C", help="Produce an object file instead of an executable", action="store_true")
    argparser.add_argument("-H", help="Produce a header file instead of an executable", action="store_true")
    argparser.add_argument("--stdout", help="Output to stdout", action="store_true")
    args = argparser.parse_args()

    import_mapping = make_import_mapping(args.im)

    if not args.infile.endswith(SOURCE_EXT):
        ERROR_HANDLER.addError(ERR.CompInputFileExtension, [SOURCE_EXT])

    if not os.path.isfile(args.infile):
        ERROR_HANDLER.addError(ERR.CompInputFileNonExist, [args.infile])

    main_mod_path = os.path.splitext(args.infile)[0]
    main_mod_name = os.path.basename(main_mod_path)

    validate_modname(main_mod_name)

    if args.o:
        outfile_base = args.o
        validate_modname(os.path.basename(outfile_base))
    else:
        outfile_base = main_mod_path


    compiler_target = {
        'header' : args.H,
        'object' : args.C,
        'binary' : not (args.H or args.C)
    }


    if args.H and args.C and args.stdout:
        ERROR_HANDLER.addError(ERR.CompInvalidArguments, ["Cannot output to stdout when creating both a headerfile and an object file!\n(-H and -C and --stdout)"])

    if args.o and args.stdout:
        ERROR_HANDLER.addError(ERR.CompInvalidArguments, ["Cannot write to specified path when outputting to stdout!\n(-o and --stdout)"])

    ERROR_HANDLER.checkpoint()

    try:
        infile = open(args.infile, "r")
    except Exception as e:
        ERROR_HANDLER.addError(ERR.CompInputFileException, [args.infile, "{} {}".format(e.__class__.__name__, str(e))], fatal=True)

    ERROR_HANDLER.setSourceMapping(infile)

    tokenstream = tokenize(infile)

    ast = parseTokenStream(tokenstream, infile)

    #print("Are there imports?",bool(ast.imports))

    #print(ast)

    if compiler_target['header']: # Generate a headerfile
        symbol_table, ext_table = buildSymbolTable(ast, main_mod_name, just_for_headerfile=True)
        #print(ext_table)
        #resolveTypeSyns(symbol_table, ext_table)
        mod_dependencies = get_type_dependencies(ast)
        header_json = export_headers(symbol_table, main_mod_name, mod_dependencies, ext_table)

        if not args.stdout:
            outfile_name = outfile_base + HEADER_EXT
            write_out(header_json, outfile_name, "headerfile")
        else:
            print(header_json)

    if compiler_target['object']: # Generate an object file
        gen_code = generateObjectFile(ast, args, main_mod_name, import_mapping)

        if not args.stdout:
            outfile_name = outfile_base + OBJECT_EXT
            write_out(gen_code, outfile_name, "objectfile")
        else:
            print(gen_code)

    if compiler_target['binary']: # Generate a binary
        gen_code = generateObjectFile(ast, args, main_mod_name, import_mapping)
        from io import StringIO
        pseudo_file_code = StringIO(gen_code)

        mod_dicts = getObjectFiles(
            pseudo_file_code,
            args.infile,
            os.path.dirname(args.infile),
            file_mapping_arg=import_mapping,
            lib_dir_path=args.lp,
            lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None
        )

        result = linkObjectFiles(mod_dicts, main_mod_name)

        if not args.stdout:
            outfile_name = outfile_base + TARGET_EXT
            write_out(result, outfile_name, "executable")
        else:
            print(result)

    # Final cleanup
    infile.close()


if __name__ == "__main__":
    main()