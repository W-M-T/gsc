#!/usr/bin/env python3

from lib.analysis.error_handler import ERROR_HANDLER
import os
import json
from AST import FunUniq

HEADER_EXT = ".spld"
OBJECT_EXT = ".splo"
SOURCE_EXT = ".spl"


'''
TODO?
add module dependency info somewhere. Either in header file or in object file
'''
def export_header_file(symbol_table):
    temp_globals = list(map(lambda x: (x.id.val, x.type.__serial__()), symbol_table.global_vars.values()))
    temp_typesyns = [(k, v.__serial__()) for (k, v) in symbol_table.type_syns.items()]
    temp_functions = [((uq.name, k), [t.__serial__() for t in v['type'].from_types], v['type'].to_type.__serial__()) for ((uq, k), v_list) in symbol_table.functions.items() for v in v_list]
    temp_packet = {
        "globals": temp_globals,
        "typesyns": temp_typesyns,
        "functions": temp_functions
        }
    return json.dumps(temp_packet, sort_keys=True,indent=2)


def import_header_file(json_string):
    temp_packet = json.loads(json_string)
    for v in temp_packet['globals']:
        print(v)
    for v in temp_packet['typesyns']:
        print(v)
    for v in temp_packet['functions']:
        v[0][0] = FunUniq[v[0][0]]
        print(v)
    temp_packet = {
        "globals": None,
        "typesyns": None,
        "functions": None
    }
    return temp_packet
'''
In order of priority:
1: File specific compiler arg
2: Library directory compiler arg
3: Environment variable
4: Local directory
'''
def resolveFileName(name, local_dir, file_mapping_arg=None, lib_dir_path=None, lib_dir_env=None):
    #print(name.name.val,local_dir)
    #option = "{}/{}.spl".format(local_dir, name)
    #print(os.path.isfile(option))

    # Try to import from the compiler argument-specified path for this specific import
    if name in file_mapping_arg:
        try:
            option = file_mapping_arg[name]
            infile = open(option)
            return infile, option
        except Exception as e:
            print(e)
    # Try to import from the compiler argument-specified directory
    if lib_dir_path is not None:
        try:
            option = "{}/{}.spl".format(lib_dir_path, name)
            infile = open(option)
            return infile, option
        except Exception as e:
            pass
    # Try to import from the environment variable-specified directory
    if lib_dir_env is not None:
        try:
            option = "{}/{}.spl".format(lib_dir_env, name)
            infile = open(option)
            return infile, option
        except Exception as e:
            pass
    # Try to import from the same directory as our source file
    try:
        option = "{}/{}.spl".format(local_dir, name)
        infile = open(option)
        return infile, option
    except Exception as e:
        pass
    raise FileNotFoundError
