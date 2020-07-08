#!/usr/bin/env python3

from argparse import ArgumentParser
from lib.imports.imports import IMPORT_DIR_ENV_VAR_NAME, OBJECT_EXT, TARGET_EXT
from lib.imports.objectfile_imports import getObjectFiles, OBJECT_COMMENT_PREFIX, OBJECT_FORMAT
from lib.analysis.error_handler import *

import os

from collections import OrderedDict
from datetime import datetime

def buildSection(mod_dicts, section_name):
    res = ""
    if section_name in SECTION_COMMENT_LOOKUP:
        res += OBJECT_COMMENT_PREFIX + SECTION_COMMENT_LOOKUP[section_name] + "\n"
    res += "\n".join(list(map(lambda x: x[section_name], mod_dicts))) + "\n"
    return res

'''
Code should have the requirement that any cross-module reference is not order dependent.
Semantic analysis step should guarantee this
'''

'''
TODO output all logging here to stderr
'''

SECTION_COMMENT_LOOKUP = {
    "global_inits": OBJECT_FORMAT['init'],
    "global_mem": OBJECT_FORMAT['globals'],
    "functions": OBJECT_FORMAT['funcs']
}
def linkObjectFiles(mod_dicts, main_mod_name):
    head = ("// SSM ASSEMBLY GENERATED ON {}".format(datetime.now().strftime("%c"))).upper()
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
    result += buildSection(mod_dicts, 'functions')
    result += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['main'] + "\n"
    result += "main: BSR {}_func_main_0\n".format(main_mod_name)
    result += "LDR RR\n"
    result += "TRAP 00\n"
    return result


def main():
    argparser = ArgumentParser(description="SPL Linker")
    #argparser.add_argument("infiles", metavar="INPUT", help="Object files to link", nargs="+", default=[])
    #argparser.add_argument("-m", "--main", metavar="NAME", help="Module to use as entrypoint", type=str)
    argparser.add_argument("infile", metavar="INPUT", help="Input file")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import object files from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated object_file:path mapping list, to explicitly specify object file paths", type=str)
    argparser.add_argument("-o", metavar="OUTPUT", help="Output filename", type=str)
    argparser.add_argument("--stdout", help="Output to stdout", action="store_true")
    args = argparser.parse_args()

    import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
    if not (all(map(lambda x: len(x)==2, import_mapping)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), import_mapping))):
        print("Invalid import mapping")
        exit()
    import_mapping = {a:b for (a,b) in import_mapping}

    if not args.infile.endswith(OBJECT_EXT):
        print("Input file needs to be {}".format(OBJECT_EXT))
        exit()

    main_mod_path = os.path.splitext(args.infile)[0]
    main_mod_name = os.path.basename(main_mod_path)

    if args.o:
        outfile_name = args.o
    else:
        outfile_name = main_mod_path + TARGET_EXT


    try:
        with open(args.infile) as infile:
            mod_dicts = getObjectFiles(
                infile,
                args.infile,
                os.path.dirname(args.infile),
                file_mapping_arg=import_mapping,
                lib_dir_path=args.lp,
                lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None
            )
    except Exception as e:
        print(e.__class__.__name__, str(e))
        exit()

    end = linkObjectFiles(mod_dicts, main_mod_name)
    #print(end)

    if not args.stdout:
        try:
            with open(outfile_name, "w") as outfile:
                outfile.write(end)
                print('Succesfully written excecutable "{}"'.format(outfile_name))
        except Exception as e:
            print(e.__class__.__name__, str(e))
    else:
        print(end)



    '''
    for struct in mod_dicts:
        for k,v in struct.items():
            print("==",k)
            print(v)
    '''
    #print(mod_dicts)
    '''
    objectfiles = getImportFiles(x, HEADER_EXT, os.path.dirname(args.infile),
                file_mapping_arg=import_mapping,
                lib_dir_path=args.lp,
                lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
                '''
    '''
    # Initial check if the files exist (does not prevent race conditions)
    if not all(map(os.path.isfile, args.infiles)):
        print("Not all input files exist!")
        exit()


    # Check if the files have the correct extension
    if not all(map(lambda x: os.path.basename(x).endswith(OBJECT_EXT), args.infiles)):
        print("Not all input files have a '{}' extension!".format(OBJECT_EXT))
        exit()
    '''
    exit()

if __name__ == "__main__":
    main()