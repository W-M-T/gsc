#!/usr/bin/env python3

from lib.imports.imports import getImportFiles, validate_modname, IMPORT_DIR_ENV_VAR_NAME, SOURCE_EXT, OBJECT_EXT, TARGET_EXT
from lib.imports.imports import export_headers, getExternalSymbols, HEADER_EXT
from lib.imports.objectfile_imports import getObjectFiles

from lib.analysis.error_handler import *

from lib.parser.lexer import tokenize, REG_FIL
from lib.parser.parser import parseTokenStream
from semantic_analysis import analyse, buildSymbolTable
from lib.codegen.codegen import generate_object_file

from gsl import linkObjectFiles, write_out, make_import_mapping

from argparse import ArgumentParser
import os


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

    print("Are there imports?",bool(ast.imports))

    #print(ast)

    if compiler_target['header']: # Generate a headerfile
        symbol_table = buildSymbolTable(ast, just_for_headerfile=True)

        header_json = export_headers(symbol_table)

        if not args.stdout:
            outfile_name = outfile_base + HEADER_EXT
            write_out(header_json, outfile_name, "headerfile")
        else:
            print(header_json)
    else:
        # Check if 
        pass

    if compiler_target['object']: # Generate an object file
        headerfiles = getImportFiles(ast, HEADER_EXT,
            os.path.dirname(args.infile),
            file_mapping_arg=import_mapping,
            lib_dir_path=args.lp,
            lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)

        a = getExternalSymbols(ast, headerfiles)
        print("EXTERNAL SYMBOLS:",a)
        exit()
        symbol_table = buildSymbolTable(ast, just_for_headerfile=False)
        '''
        symbol_table = analyse(ast, main_mod_name)

        assembly = generate_object_file(symbol_table, main_mod_name)
        '''
        '''
        headerfiles = getImportFiles(x, HEADER_EXT, os.path.dirname(args.infile),
            file_mapping_arg=import_mapping,
            lib_dir_path=args.lp,
            lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        a = getExternalSymbols(x, headerfiles)
        print(a)
        exit()
        '''
    if compiler_target['binary']: # Generate a binary
        # insert zelfde code als bij begin van compiler_target['object']
        # maak er gewoon een functie van

        # dan
        from io import StringIO
        compiled_code = '''// DEPENDENCIES:
// DEPEND testlinkB
// INIT SECTION:
LDC 9
LDC 4
ADD
LDC testlinkA_global_b
STA 00
LDC 5
LDC testlinkA_global_a
STA 00
// ENTRYPOINT:
BRA main
// GLOBAL SECTION:
testlinkA_global_b: NOP
testlinkA_global_a: NOP
// FUNCTION SECTION:
testlinkA_func_main_0: LINK 00
LDC testlinkA_global_a
LDA 00
LDL 1
LDL 1
LDL 2
ADD
STR RR
UNLINK
RET
// MAIN:
main: BSR testlinkA_func_main_0
LDR RR
BSR testlinkB_func_main_0
LDR RR
ADD
TRAP 00'''
        pseudo_file_code = StringIO(compiled_code)
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
            write_out(end, outfile_name, "executable")
        else:
            print(result)

    # Final cleanup
    infile.close()


if __name__ == "__main__":
    main()