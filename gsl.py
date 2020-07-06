#!/usr/bin/env python3

from argparse import ArgumentParser
from lib.imports.imports import resolveFileName, SOURCE_EXT, OBJECT_EXT, TARGET_EXT
import os

from collections import OrderedDict

'''
TODO Validate filenames using REG_FIL from lexer
'''

OBJECT_COMMENT_PREFIX = "// "

OBJECT_FORMAT = {
    "depend"    : "DEPENDENCIES:",
    "dependitem": "DEPEND ",
    "init"      : "INIT SECTION:",
    "entrypoint": "ENTRYPOINT:",
    "globals"   : "GLOBAL SECTION:",
    "funcs"     : "FUNCTION SECTION:",
    "main"      : "MAIN:"
}

def getSlice(text, start, end):
    start_ix = text.find(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT[start]) if start is not None else 0
    end_ix = text.find(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT[end]) if end is not None else len(text)
    if start_ix == -1 or end_ix == -1:
        raise Exception("Malformed object file")
    res = text[start_ix:end_ix].split("\n",1)[1]
    text = text[:start_ix] + text[end_ix:]
    return res, text

def parseObjectFile(data):# This function is jank and needs refactor
    deps, data = getSlice(data, "depend", "init")
    inits, data = getSlice(data, "init", "entrypoint")
    globs, data = getSlice(data, "globals", "funcs")
    funcs, data = getSlice(data, "funcs", "main")
    main, data = getSlice(data, "main", None)

    modnames = set()
    for line in [x for x in deps.split("\n") if len(x) > 0]:
        if line.startswith(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['dependitem']):
            found = line[len(OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['dependitem']):]
            modnames.add(found)
        elif line.startswith(OBJECT_COMMENT_PREFIX):
            pass
        else:
            raise Exception("Malformed "+line)
    modnames = list(modnames)
    #print(modnames)
    temp = OrderedDict([
        ("dependencies", modnames),
        ("global_inits", inits),
        ("global_mem", globs),
        ("functions", funcs)
    ])
    return temp

'''
def getAllObjectFiles(filehandle):
    data = filehandle.read()
    res = parseObjectFile(data)
    for k,v in res.items():
        print(k)
        print(v)
'''

def getObjectFiles(main_filename, local_dir, file_mapping_arg={}, lib_dir_path=None, lib_dir_env=None):
    #unique_names = list(OrderedDict.fromkeys(map(lambda x: x, parsed_main['dependencies']))) # order preserving uniqueness
    #print(importlist)
    print("CWD",local_dir)
    print("--lp",lib_dir_path)
    print("env",lib_dir_env)

    seen = set()
    closed = {}
    openlist = []
    while openlist:
        cur = openlist.pop()
        for impname in unique_names:
            try:
                handle, path = resolveFileName(impname, OBJECT_EXT, local_dir, file_mapping_arg=file_mapping_arg, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
                data = handle.read()
                obj_struct = parseObjectFile(data)
                for name in obj_struct['dependencies']:
                    pass

                temp[impname] = {"name":impname,"filehandle":handle,"path":path}
            except Exception as e:
                #ERROR_HANDLER.addError(ERR.ImportNotFound, [impname, "\t" + "\n\t".join(str(e).split("\n"))])
                print("ERROR TODO")
                exit()

    ERROR_HANDLER.checkpoint()
    return temp


def buildSection(mod_dicts, section_name):
    return "\n".join(list(map(lambda x: x[section_name], mod_dicts)))

'''
Code should have the requirement that any cross-module reference is not order dependent.
Semantic analysis step should guarantee this
'''
def linkObjectFiles(mod_dicts, main_mod_name):
    result = ""
    result += buildSection(mod_dicts, 'global_inits')
    result += "BRA main\n"
    result += buildSection(mod_dicts, 'global_mem')
    result ++ buildSection(mod_dicts, 'functions')
    result += "main: nop\n"
    result += "LDR RR\n"
    result ++ "TRAP 00\n"
    return result


def main():
    argparser = ArgumentParser(description="SPL Linker")
    #argparser.add_argument("infiles", metavar="INPUT", help="Object files to link", nargs="+", default=[])
    #argparser.add_argument("-m", "--main", metavar="NAME", help="Module to use as entrypoint", type=str)
    argparser.add_argument("infile", metavar="INPUT", help="Input file")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import object files from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated object_file:path mapping list, to explicitly specify object file paths", type=str)
    argparser.add_argument("-o", metavar="OUTPUT", help="Output filename", type=str)
    args = argparser.parse_args()

    import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
    if not (all(map(lambda x: len(x)==2, import_mapping)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), import_mapping))):
        print("Invalid import mapping")
        exit()

    '''
    if not args.infile.endswith(OBJECT_EXT):
        print("Input file needs to be {}".format(OBJECT_EXT))
        exit()

    if not os.path.isfile(args.infile):
        print("Input file does not exist: {}".format(args.infile))
        exit()
    '''

    mod_dicts = getObjectFiles(args.infile)
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

    # Open all input files
    handle_dict = {}
    try:
        for filename in args.infiles:
            temp_handle = open(filename,"r")
            handle_dict[filename] = temp_handle
    except Exception as e:
        print("Error opening input files:")
        print(e)

    link(handle_dict)

    # Close the input files
    for k,v in handle_dict.items():
        v.close()


if __name__ == "__main__":
    main()