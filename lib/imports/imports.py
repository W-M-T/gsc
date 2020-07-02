#!/usr/bin/env python3

from lib.imports.header_parser import parse_type
import json
from lib.datastructure.AST import FunUniq, AST
from lib.analysis.error_handler import *
import os

HEADER_EXT = ".spld"
OBJECT_EXT = ".splo"
SOURCE_EXT = ".spl"

'''
Voorbeeld:
A import B
B import C
object file van B bevat bytecode voor B en C
zdd het linken van A alleen de object file van B nodig heeft
'''
'''
TODO?
add module dependency info somewhere. Either in header file or in object file
'''
def export_headers(symbol_table):
    temp_globals = list(map(lambda x: (x.id.val, x.type.__serial__()), symbol_table.global_vars.values()))
    temp_typesyns = [(k, v.__serial__()) for (k, v) in symbol_table.type_syns.items()]
    temp_functions = [((uq.name, k), [t.__serial__() for t in v['type'].from_types], v['type'].to_type.__serial__()) for ((uq, k), v_list) in symbol_table.functions.items() for v in v_list]
    temp_packet = {
        "globals": temp_globals,
        "typesyns": temp_typesyns,
        "functions": temp_functions
        }
    return json.dumps(temp_packet, sort_keys=True,indent=2)


def import_headers(json_string): # Can return exception, so put in try-except
    temp_packet = json.loads(json_string)
    temp_packet["globals"] = {k:parse_type(v) for k,v in temp_packet["globals"]}
    temp_packet["typesyns"] = {k:parse_type(v) for k,v in temp_packet["typesyns"]}
    temp_packet["functions"] = {(FunUniq[uq], k):
                                    AST.FUNTYPE(from_types=list(map(parse_type,from_ts)), to_type=parse_type(to_t))
                                    for (uq, k),from_ts,to_t in temp_packet["functions"]}
    return temp_packet

'''
In order of priority:
1: File specific compiler arg
2: Library directory compiler arg
3: Environment variable
4: Local directory
'''
def resolveFileName(name, extension, local_dir, file_mapping_arg={}, lib_dir_path=None, lib_dir_env=None):
    fullname = "{}{}".format(name, extension)
    exception_list = []
    # Try to import from the compiler argument-specified path for this specific import
    if name in file_mapping_arg:
        try:
            try_path = file_mapping_arg[name] + extension
            infile = open(try_path)
            print("Found through mapping")
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
    else:
        print(name,"not in mapping")
    # Try to import from the compiler argument-specified directory
    if lib_dir_path is not None:
        try:
            try_path = os.path.join(lib_dir_path, name)
            print(try_path)
            infile = open(try_path)
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
    # Try to import from the environment variable-specified directory
    if lib_dir_env is not None:
        try:
            try_path = os.path.join(lib_dir_env, name)
            infile = open(try_path)
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
    # Try to import from the same directory as our source file
    try:
        try_path = os.path.join(local_dir, name) + extension
        #print(try_path)
        infile = open(try_path)
        return infile, try_path
    except Exception as e:
        exception_list.append(e)
    raise FileNotFoundError("\n".join(list(map(lambda x: "{}: {}".format(x.__class__.__name__,str(x)),exception_list))))

def getImportFiles(ast, extension, local_dir, file_mapping_arg={}, lib_dir_path=None, lib_dir_env=None):
    importlist = ast.imports
    print(importlist)
    print("CWD",local_dir)
    print("--lp",lib_dir_path)
    print("env",lib_dir_env)

    temp = []
    for imp in importlist:
        impname = imp.name.val
        try:
            handle, path = resolveFileName(impname, extension, local_dir, file_mapping_arg=file_mapping_arg, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
            temp.append({"name":impname,"filehandle":handle,"path":path})
        except Exception as e:
            ERROR_HANDLER.addError(ERR.ImportNotFound, [impname, "\t" + "\n\t".join(str(e).split("\n"))])

    ERROR_HANDLER.checkpoint()
    return temp
