#!/usr/bin/env python3

from argparse import ArgumentParser
from lib.imports.imports import validate_modname, IMPORT_DIR_ENV_VAR_NAME, OBJECT_EXT, TARGET_EXT
from lib.imports.objectfile_imports import getObjectFiles, OBJECT_COMMENT_PREFIX, OBJECT_FORMAT
from lib.analysis.error_handler import *

import os

from collections import OrderedDict
from datetime import datetime


BUILTIN_FUNC_BODIES = {
    'head':
        [
            'LINK 00',
            'LDL -2',
            'LDC 00',
            'EQ',
            'BRT program_crash',
            'LDL -2',
            'LDH -1',
            'STR RR',
            'UNLINK',
            'RET'
        ],
    'tail':
        [
            'LINK 00',
            'LDL -2',
            'LDC 00',
            'EQ',
            'BRT program_crash',
            'LDL -2',
            'LDH 00',
            'STR RR',
            'UNLINK',
            'RET',
        ],
    'print_string':
        [
            'LINK 00',
            'BRA print_string_loop'
        ],
    'print_string_loop':
        [
            'LDL -2',
            'LDC 00',
            'EQ',
            'NOT',
            'BRF print_string_exit',
            'LDL -2',
            'BSR head',
            'AJS -1',
            'LDR RR',
            'TRAP 1',
            'LDL -2',
            'BSR tail',
            'AJS -1',
            'LDR RR',
            'STL -2',
            'BRA print_string_loop',
        ],
    'print_string_exit':
        [
            'UNLINK',
            'RET'
        ]
}

def getEntryPointName(module_name):
    return "{}_func_main_0".format(module_name)

def makeEntryPoint(module_name):
    temp = "\n".join([
        'main: BSR {}'.format(getEntryPointName(module_name)),
        'LDR RR',
        'TRAP 00',
        'HALT',
        'program_crash: LDC 67',
        'LDC 82',
        'LDC 65',
        'LDC 83',
        'LDC 72',
        'LDC 58',
        'LDC 32',
        'LDC 68',
        'LDC 69',
        'LDC 82',
        'LDC 69',
        'LDC 70',
        'LDC 32',
        'LDC 91',
        'LDC 93',
        'LDC 00',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'STMH 2',
        'BSR print_string'
    ])
    return temp


def buildSection(mod_dicts, section_name):
    res = ""
    if section_name in SECTION_COMMENT_LOOKUP:
        res += OBJECT_COMMENT_PREFIX + SECTION_COMMENT_LOOKUP[section_name] + "\n"
    res += "\n".join(list(map(lambda x: x[section_name], mod_dicts))).lstrip() + "\n"
    if section_name == "functions":
        for func_name, instructions in BUILTIN_FUNC_BODIES.items():
            res += func_name + ":" + "\n".join(instructions) + "\n"
    return res


'''
Code should have the requirement that any cross-module reference is not order dependent.
Semantic analysis step should guarantee this
'''


SECTION_COMMENT_LOOKUP = {
    "global_inits": OBJECT_FORMAT['init'],
    "global_mem": OBJECT_FORMAT['globals'],
    "functions": OBJECT_FORMAT['funcs']
}
def linkObjectFiles(mod_dicts, main_mod_name):
    head = ("// SSM ASSEMBLY GENERATED ON {}".format(datetime.now().strftime("%c"))).upper()
    func_text = buildSection(mod_dicts, 'functions')
    right_main_present = func_text.find(getEntryPointName(main_mod_name)) != -1
    if not right_main_present:
        ERROR_HANDLER.addError(ERR.CompilerNoEntrypointPresent, [main_mod_name])
        ERROR_HANDLER.checkpoint()

    sep_line = "//" + "="*(len(head)-2)+"\n"
    result = ""
    result += sep_line
    result += head + "\n"
    result += "// © Ward Theunisse & Ischa Stork 2020\n"
    result += sep_line
    result += buildSection(mod_dicts, 'global_inits')
    result += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['entrypoint'] + "\n"
    result += "BRA main\n"
    result += buildSection(mod_dicts, 'global_mem')
    result += func_text
    result += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['main'] + "\n"
    result += makeEntryPoint(main_mod_name)
    return result

def write_out(data, outfile_name, type_name):
    try:
        with open(outfile_name, "w") as outfile:
            outfile.write(data)
            print('Succesfully written {} "{}"'.format(type_name, outfile_name))
    except Exception as e:
        ERROR_HANDLER.addError(ERR.CompOutputFileException, [outfile_name, "{} {}".format(e.__class__.__name__, str(e))], fatal=True)

def make_import_mapping(im):
    temp = list(map(lambda x: x.split(":", 1), im.split(","))) if im is not None else []
    if not (all(map(lambda x: len(x)==2, temp)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), temp))):
        ERROR_HANDLER.addError(ERR.CompInvalidImportMapping, [], fatal=True)
    for a,b in temp:
        validate_modname(a)
    temp = {a:b for (a,b) in temp}
    return temp


def main():
    argparser = ArgumentParser(description="SPL Linker")
    argparser.add_argument("infile", metavar="INPUT", help="Input file")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import object files from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated object_file:path mapping list, to explicitly specify object file paths", type=str)
    argparser.add_argument("-o", metavar="OUTPUT", help="Output filename", type=str)
    argparser.add_argument("--stdout", help="Output to stdout", action="store_true")
    args = argparser.parse_args()

    import_mapping = make_import_mapping(args.im)

    if not args.infile.endswith(OBJECT_EXT):
        ERROR_HANDLER.addError(ERR.CompInputFileExtension, [OBJECT_EXT])

    if not os.path.isfile(args.infile):
        ERROR_HANDLER.addError(ERR.CompInputFileNonExist, [args.infile])


    main_mod_path = os.path.splitext(args.infile)[0]
    main_mod_name = os.path.basename(main_mod_path)

    validate_modname(main_mod_name)

    if args.o:
        outfile_name = args.o
        validate_modname(os.path.basename(outfile_base))
    else:
        outfile_name = main_mod_path + TARGET_EXT

    if args.o and args.stdout:
        ERROR_HANDLER.addError(ERR.CompInvalidArguments, ["Cannot write to specified path when outputting to stdout!\n(-o and --stdout)"])

    ERROR_HANDLER.checkpoint()

    # Open input file, get all object files
    try:
        infile = open(args.infile, "r")
    except Exception as e:
        ERROR_HANDLER.addError(ERR.CompInputFileException, [args.infile, "{} {}".format(e.__class__.__name__, str(e))], fatal=True)
    mod_dicts = getObjectFiles(
        infile,
        args.infile,
        os.path.dirname(args.infile),
        file_mapping_arg=import_mapping,
        lib_dir_path=args.lp,
        lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None
    )
    infile.close()

    end = linkObjectFiles(mod_dicts, main_mod_name)
    #print(end)

    if not args.stdout:
        write_out(end, outfile_name, "executable")
    else:
        print(end)

    '''
    for struct in mod_dicts:
        for k,v in struct.items():
            print("==",k)
            print(v)
    '''
    #print(mod_dicts)



if __name__ == "__main__":
    main()