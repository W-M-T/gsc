#!/usr/bin/env python3

from lib.imports.header_parser import parse_type
import json
from lib.datastructure.AST import FunUniq, AST
from lib.datastructure.token import TOKEN
from lib.analysis.error_handler import *
import os
from collections import OrderedDict

HEADER_EXT = ".spld"
OBJECT_EXT = ".splo"
SOURCE_EXT = ".spl"
TARGET_EXT = ".ssm"

'''
TODO Validate filenames using REG_FIL from lexer
'''

'''
TODO?
add module dependency info somewhere. Either in header file or in object file
'''
def export_headers(symbol_table):
    temp_globals = list(map(lambda x: (x.id.val, x.type.__serial__()), symbol_table.global_vars.values()))
    temp_typesyns = [(k, v.__serial__()) for (k, v) in symbol_table.type_syns.items()]
    temp_functions = [((uq.name, k),
        v['def'].fixity.val if v['def'].fixity is not None else None,
        v['def'].kind.name,
        [t.__serial__() for t in v['type'].from_types], v['type'].to_type.__serial__()) for ((uq, k), v_list) in symbol_table.functions.items() for v in v_list]
    temp_packet = {
        "globals": temp_globals,
        "typesyns": temp_typesyns,
        "functions": temp_functions
    }
    return json.dumps(temp_packet, sort_keys=True,indent=2)


def import_headers(json_string): # Can return exception, so put in try-except
    load_packet = json.loads(json_string)
    temp_packet = {}
    temp_packet["globals"] = {k:parse_type(v) for k,v in load_packet["globals"]}
    temp_packet["typesyns"] = {k:parse_type(v) for k,v in load_packet["typesyns"]}
    temp_packet["functions"] = {}
    for (uq, k),fix,kind,from_ts,to_t in load_packet["functions"]:
        if (FunUniq[uq], k) not in temp_packet["functions"]:
            temp_packet["functions"][(FunUniq[uq], k)] = []
        temp_packet["functions"][(FunUniq[uq], k)].append({
            "fixity":fix,
            "kind":kind,
            "type":AST.FUNTYPE(from_types=list(map(parse_type,from_ts)), to_type=parse_type(to_t))
        })

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
            #print("Found through mapping")
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
    else:
        #print(name,"not in mapping")
        pass
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

    unique_names = list(OrderedDict.fromkeys(map(lambda x: x.name.val, importlist))) # order preserving uniqueness
    print(importlist)
    print("CWD",local_dir)
    print("--lp",lib_dir_path)
    print("env",lib_dir_env)

    temp = {}
    for impname in unique_names:
        try:
            handle, path = resolveFileName(impname, extension, local_dir, file_mapping_arg=file_mapping_arg, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
            temp[impname] = {"name":impname,"filehandle":handle,"path":path}
        except Exception as e:
            ERROR_HANDLER.addError(ERR.ImportNotFound, [impname, "\t" + "\n\t".join(str(e).split("\n"))])

    ERROR_HANDLER.checkpoint()
    return temp

'''
Parse a list of headerfiles to json and subset the symbols that are in scope
'''
def getExternalSymbols(ast, headerfiles):
    importlist = ast.imports

    # Read all headerfiles
    #print("Headerfiles",headerfiles)
    for head in headerfiles.values():
        data = head['filehandle'].read()
        #try:
        symbols = import_headers(data)
        #print(symbols)
        #exit()
        head['symbols'] = symbols
        #except Exception as e:
        #    ERROR_HANDLER.addError(ERR.HeaderFormatIncorrect, [head['path'], "\t{}: {}".format(e.__class__.__name__,str(e))])

    # Close all the opened filehandles
    for head in headerfiles.values():
        head['filehandle'].close()
    ERROR_HANDLER.checkpoint()

    # Add the desired imports to a datastructure
    external_symbols = {
        # Effective identifier to dict with type, module and original identifier
        'globals':{},
        # Effective identifier to dict with type, module and original identifier
        'typesyns':{},
        # (FunUniq, Effective identifier) to list with (dict with type, module and original identifier)
        'functions':{}
    }

    # Collect all imports for the same module and give warnings
    unique_names = list(OrderedDict.fromkeys(map(lambda x: x.name.val, importlist))) # order preserving uniqueness
    for modname in unique_names:
        cur_imports = list(filter(lambda x: x.name.val == modname, importlist))
        print(modname,cur_imports)

        # Test if there is both an importall and another import for the same module
        if any(map(lambda x: x.importlist is None, cur_imports)) and len(cur_imports) > 1:
            ERROR_HANDLER.addWarning(WARN.MultiKindImport, [modname, cur_imports])
            ERROR_HANDLER.checkpoint()

        # Combine all other imports for this module
        all_cur_imports = [item for x in cur_imports if x.importlist is not None for item in x.importlist]
        #print("ALL CUR:",all_cur_imports)

        id_imports = list(filter(lambda x: x.name.typ == TOKEN.IDENTIFIER, all_cur_imports))
        op_imports = list(filter(lambda x: x.name.typ == TOKEN.OP_IDENTIFIER, all_cur_imports))
        type_imports = list(filter(lambda x: x.name.typ == TOKEN.TYPE_IDENTIFIER, all_cur_imports))
        #print("ALL ID:",id_imports)
        #print("ALL OP:",op_imports)
        #print("ALL TYPE:",type_imports)

        # Test for identifiers that are imported multiple times
        # Also, select the desired symbols and give error if they don't exist
        cur_symbols = headerfiles[modname]['symbols']
        print("SYMBOLS",cur_symbols)
        unique_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, id_imports)))
        unique_op_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, op_imports)))
        unique_type_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, type_imports)))

        for uq_id in unique_ids:
            matching = list(filter(lambda x: x.name.val == uq_id, id_imports))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateIdSameModuleImport, [uq_id, modname, list(map(lambda x: x.name,matching))])

            for match in matching:
                match_orig = match.name.val
                effective_id = match.alias.val if match.alias is not None else match_orig

                if match_orig in cur_symbols['globals'] or (FunUniq.FUNC, match_orig) in cur_symbols['functions']: # Try to import id that exists in the header
                    if match_orig in cur_symbols['globals']:
                        found_global = cur_symbols['globals'][match_orig]

                        if effective_id not in external_symbols['globals']: # New name for global
                            external_symbols['globals'][effective_id] = {
                                'type': found_global,
                                'module': modname,
                                'orig_id': match_orig
                            }
                        else:
                            ERROR_HANDLER.addError(ERR.ClashImportGlobal, [effective_id, match.name if match.alias is None else match.alias])
                    if (FunUniq.FUNC, match_orig) in cur_symbols['functions']:
                        found_funcs = cur_symbols['functions'][(FunUniq.FUNC, match_orig)]
                        #print("found_funcs",found_funcs)
                else:
                    ERROR_HANDLER.addError(ERR.ImportIdentifierNotFound, [uq_id, modname, headerfiles[modname]['path']])


        for uq_op_id in unique_op_ids:
            matching = list(filter(lambda x: x.name.val == uq_op_id, op_imports))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateOpSameModuleImport, [uq_op_id, modname, list(map(lambda x: x.name,matching))])

            if (FunUniq.PREFIX, uq_op_id) in cur_symbols['functions']:
                pass
            elif (FunUniq.INFIX, uq_op_id) in cur_symbols['functions']:
                pass
            else:
                ERROR_HANDLER.addError(ERR.ImportOpIdentifierNotFound, [uq_op_id, modname, headerfiles[modname]['path']])


        for uq_type_id in unique_type_ids:
            matching = list(filter(lambda x: x.name.val == uq_type_id, type_imports))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateTypeSameModuleImport, [uq_type_id, modname, list(map(lambda x: x.name,matching))])

            for match in matching:
                #print("MATCH",match)
                match_orig = match.name.val
                effective_id = match.alias.val if match.alias is not None else match_orig

                if match_orig in cur_symbols['typesyns']:
                    found = cur_symbols['typesyns'][match_orig]

                    if effective_id not in external_symbols['typesyns']: # New name
                        external_symbols['typesyns'][effective_id] = {
                            'type': found,
                            'module': modname,
                            'orig_id': match_orig
                        }
                    else:
                        ERROR_HANDLER.addError(ERR.ClashImportType, [effective_id, match.name if match.alias is None else match.alias])
                else:
                    ERROR_HANDLER.addError(ERR.ImportTypeSynNotFound, [uq_type_id, modname, headerfiles[modname]['path']])

        ERROR_HANDLER.checkpoint()