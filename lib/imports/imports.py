#!/usr/bin/env python3

from lib.imports.header_parser import parse_type
import json
from lib.datastructure.AST import FunUniq, AST
from lib.datastructure.token import TOKEN
from lib.datastructure.symbol_table import ExternalTable
from lib.analysis.error_handler import *

from collections import OrderedDict
from lib.parser.lexer import REG_FIL
from lib.builtins.builtin_mod import BUILTINS_NAME

import os

HEADER_EXT = ".spld"
OBJECT_EXT = ".splo"
SOURCE_EXT = ".spl"
TARGET_EXT = ".ssm"

IMPORT_DIR_ENV_VAR_NAME = "SPL_PATH"

RESERVED_MODNAMES = [
    BUILTINS_NAME
]

'''
everything breaks if the object files linked with are generated from a different version of a source file than its headerfile
solution: have headerfile and object file encode the md5sum of their source file + add this md5sum after the module name for each dependency in the object file
'''

def validate_modname(mod_name): # Errors need to be collected outside
    if not REG_FIL.fullmatch(mod_name):
        ERROR_HANDLER.addError(ERR.CompModuleFileNameRegex, [mod_name])
    if mod_name in RESERVED_MODNAMES:
        ERROR_HANDLER.addError(ERR.ReservedModuleName, [mod_name])

def export_headers(symbol_table):
    temp_globals = list(map(lambda x: (x.id.val, x.type.__serial__()), symbol_table.global_vars.values()))
    temp_typesyns = [(k, v['def_type'].__serial__()) for (k, v) in symbol_table.type_syns.items()]
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
    temp_packet["globals"] = OrderedDict([(k,parse_type(v)) for k,v in load_packet["globals"]])
    temp_packet["typesyns"] = OrderedDict([(k,parse_type(v)) for k,v in load_packet["typesyns"]])
    temp_packet["functions"] = OrderedDict()
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
    exception_list = []
    # Try to import from the compiler argument-specified path for this specific import
    if name in file_mapping_arg:
        # Exact path
        try:
            try_path = file_mapping_arg[name]
            infile = open(try_path)
            #print("Found through mapping")
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
        # Path with forced extension
        try:
            try_path = os.path.splitext(file_mapping_arg[name])[0] + extension
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
            try_path = os.path.join(lib_dir_path, name) + extension
            #print(try_path)
            infile = open(try_path)
            return infile, try_path
        except Exception as e:
            exception_list.append(e)
    # Try to import from the environment variable-specified directory
    if lib_dir_env is not None:
        try:
            try_path = os.path.join(lib_dir_env, name) + extension
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
    raise FileNotFoundError("\n".join(list(map(lambda x: "{}: {}".format(x.__class__.__name__,str(x)), exception_list))))

'''
Get the files to import as found in the ast
'''
def getImportFiles(ast, extension, local_dir, file_mapping_arg={}, lib_dir_path=None, lib_dir_env=None):
    importlist = ast.imports

    unique_names = list(OrderedDict.fromkeys(map(lambda x: x.name.val, importlist))) # order preserving uniqueness
    #print(importlist)
    #print("CWD",local_dir)
    #print("--lp",lib_dir_path)
    #print("env",lib_dir_env)

    temp = {}
    for impname in unique_names:
        validate_modname(impname)
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
        '''
        for key in sorted(list(symbols)):
            print(symbols[key])
        '''
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
    ext_symbol_table = ExternalTable()

    # Collect all imports for the same module and give warnings
    unique_names = list(OrderedDict.fromkeys(map(lambda x: x.name.val, importlist))) # order preserving uniqueness
    for modname in unique_names:
        cur_imports = list(filter(lambda x: x.name.val == modname, importlist))
        importall_present = False

        # Test if there is both an importall and another import for the same module
        if any(map(lambda x: x.importlist is None, cur_imports)) and len(cur_imports) > 1:
            ERROR_HANDLER.addWarning(WARN.MultiKindImport, [modname, cur_imports])

        # Combine all other import statements for this module
        all_cur_imports = [item for x in cur_imports if x.importlist is not None for item in x.importlist]

        if any([x.importlist is None for x in cur_imports]):
            #print(modname,"importall")
            importall_present = True
            importall_statement = list(filter(lambda x: x.importlist is None, cur_imports))[0]
        #print("ALL CUR:",all_cur_imports)

        # Check for cross-type aliasing (forbidden because missing fixities for operators, a.o.)
        for imp_statement in all_cur_imports:
            if imp_statement.alias is not None:
                if imp_statement.name.typ != imp_statement.alias.typ: # Identifier aliased as different identifier type
                    ERROR_HANDLER.addError(ERR.ImportIdChangeType, [imp_statement.name.val, imp_statement.name.typ.name, imp_statement.alias.typ.name, imp_statement.name])
        #ERROR_HANDLER.checkpoint()


        id_imports = list(filter(lambda x: x.name.typ == TOKEN.IDENTIFIER, all_cur_imports))
        op_imports = list(filter(lambda x: x.name.typ == TOKEN.OP_IDENTIFIER, all_cur_imports))
        type_imports = list(filter(lambda x: x.name.typ == TOKEN.TYPE_IDENTIFIER, all_cur_imports))
        #print("ALL ID:",id_imports)
        #print("ALL OP:",op_imports)
        #print("ALL TYPE:",type_imports)

        # Test for identifiers that are imported multiple times
        # Also, select the desired symbols and give error if they don't exist
        cur_symbols = headerfiles[modname]['symbols']

        #print("SYMBOLS",cur_symbols)
        if not importall_present:
            unique_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, id_imports)))
            unique_op_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, op_imports)))
            unique_type_ids = list(OrderedDict.fromkeys(map(lambda x: x.name.val, type_imports)))
        else:
            unique_ids = cur_symbols["globals"]
            unique_op_ids = list(map(lambda y: y[0][1], filter(lambda x: x[0][0] == FunUniq.PREFIX or x[0][0] == FunUniq.INFIX, cur_symbols["functions"].items())))
            unique_type_ids = list(cur_symbols["typesyns"])

        
        for uq_id in unique_ids: # Globals and functions

            matching = list(filter(lambda x: x.name.val == uq_id, id_imports))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateIdSameModuleImport, [uq_id, modname, list(map(lambda x: x.name,matching))])

            if importall_present: # General import / Importall:
                if uq_id in cur_symbols['globals']:
                    found_global = cur_symbols['globals'][uq_id]
                    if uq_id not in ext_symbol_table.global_vars: # New name for global
                        ext_symbol_table.global_vars[uq_id] = {
                            'type': found_global,
                            'module': modname,
                            'orig_id': uq_id
                        }
                    else:
                        ERROR_HANDLER.addError(ERR.ClashImportGlobal, [uq_id, importall_statement])

                if (FunUniq.FUNC, uq_id) in cur_symbols['functions']:
                        found_funcs = cur_symbols['functions'][(FunUniq.FUNC, uq_id)]
                        #print("Found_funcs",match_orig,found_funcs)

                        add_entries = list(map(lambda x: {
                                'type': x['type'],
                                'module': modname,
                                'orig_id': uq_id,
                                'fixity': x['fixity'],
                                'kind': x['kind']
                            }, found_funcs))

                        if (FunUniq.FUNC, uq_id) not in ext_symbol_table.functions: # New name for function (note that we can only forbid duplicates after type normalisation)
                            ext_symbol_table.functions[(FunUniq.FUNC, uq_id)] = []

                        ext_symbol_table.functions[(FunUniq.FUNC, uq_id)].extend(add_entries)


            for match in matching: # Specific imports
                match_orig = match.name.val
                effective_id = match.alias.val if match.alias is not None else match_orig

                if match_orig in cur_symbols['globals'] or (FunUniq.FUNC, match_orig) in cur_symbols['functions']: # Try to import id that exists in the header
                    if match_orig in cur_symbols['globals']:
                        #print("Found global",match_orig)
                        found_global = cur_symbols['globals'][match_orig]

                        if effective_id not in ext_symbol_table.global_vars: # New name for global
                            ext_symbol_table.global_vars[effective_id] = {
                                'type': found_global,
                                'module': modname,
                                'orig_id': match_orig
                            }
                        else:
                            ERROR_HANDLER.addError(ERR.ClashImportGlobal, [effective_id, match.name if match.alias is None else match.alias])

                    if (FunUniq.FUNC, match_orig) in cur_symbols['functions']:
                        found_funcs = cur_symbols['functions'][(FunUniq.FUNC, match_orig)]
                        #print("Found_funcs",match_orig,found_funcs)

                        add_entries = list(map(lambda x: {
                                'type': x['type'],
                                'module': modname,
                                'orig_id': match_orig,
                                'fixity': x['fixity'],
                                'kind': x['kind']
                            }, found_funcs))

                        if (FunUniq.FUNC, effective_id) not in ext_symbol_table.functions: # New name for function (note that we can only forbid duplicates after type normalisation)
                            ext_symbol_table.functions[(FunUniq.FUNC, effective_id)] = []

                        ext_symbol_table.functions[(FunUniq.FUNC, effective_id)].extend(add_entries)

                else:
                    ERROR_HANDLER.addError(ERR.ImportIdentifierNotFound, [match_orig, modname, headerfiles[modname]['path']])


        for uq_op_id in unique_op_ids: # Operators

            matching = list(filter(lambda x: x.name.val == uq_op_id, op_imports))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateOpSameModuleImport, [uq_op_id, modname, list(map(lambda x: x.name,matching))])

            if importall_present: # General import / Importall
                # TODO this code should be deduplicated
                if (FunUniq.PREFIX, uq_op_id) in cur_symbols['functions']:
                    found_op_in_headerfile = True
                    found_prefix_ops = cur_symbols['functions'][(FunUniq.PREFIX, uq_op_id)]

                    add_entries = list(map(lambda x: {
                            'type': x['type'],
                            'module': modname,
                            'orig_id': uq_op_id,
                            'fixity': x['fixity'],
                            'kind': x['kind']
                        }, found_prefix_ops))

                    if (FunUniq.PREFIX, uq_op_id) not in ext_symbol_table.functions: # New name for prefix op (note that we can only forbid duplicates after type normalisation)
                        ext_symbol_table.functions[(FunUniq.PREFIX, uq_op_id)] = []

                    ext_symbol_table.functions[(FunUniq.PREFIX, uq_op_id)].extend(add_entries)

                if (FunUniq.INFIX, uq_op_id) in cur_symbols['functions']:
                    found_op_in_headerfile = True
                    found_infix_ops = cur_symbols['functions'][(FunUniq.INFIX, uq_op_id)]

                    add_entries = list(map(lambda x: {
                            'type': x['type'],
                            'module': modname,
                            'orig_id': uq_op_id,
                            'fixity': x['fixity'],
                            'kind': x['kind']
                        }, found_infix_ops))

                    if (FunUniq.INFIX, uq_op_id) not in ext_symbol_table.functions: # New name for infix op (note that we can only forbid duplicates after type normalisation)
                        ext_symbol_table.functions[(FunUniq.INFIX, uq_op_id)] = []

                    ext_symbol_table.functions[(FunUniq.INFIX, uq_op_id)].extend(add_entries)

                if not found_op_in_headerfile:
                    ERROR_HANDLER.addError(ERR.ImportOpIdentifierNotFound, [uq_op_id, modname, headerfiles[modname]['path']])


            for match in matching:
                match_orig = match.name.val
                effective_id = match.alias.val if match.alias is not None else match_orig

                found_op_in_headerfile = False

                if (FunUniq.PREFIX, match_orig) in cur_symbols['functions']:
                    found_op_in_headerfile = True
                    found_prefix_ops = cur_symbols['functions'][(FunUniq.PREFIX, match_orig)]

                    add_entries = list(map(lambda x: {
                            'type': x['type'],
                            'module': modname,
                            'orig_id': match_orig,
                            'fixity': x['fixity'],
                            'kind': x['kind']
                        }, found_prefix_ops))

                    if (FunUniq.PREFIX, effective_id) not in ext_symbol_table.functions: # New name for prefix op (note that we can only forbid duplicates after type normalisation)
                        ext_symbol_table.functions[(FunUniq.PREFIX, effective_id)] = []

                    ext_symbol_table.functions[(FunUniq.PREFIX, effective_id)].extend(add_entries)

                if (FunUniq.INFIX, match_orig) in cur_symbols['functions']:
                    found_op_in_headerfile = True
                    found_infix_ops = cur_symbols['functions'][(FunUniq.INFIX, match_orig)]

                    add_entries = list(map(lambda x: {
                            'type': x['type'],
                            'module': modname,
                            'orig_id': match_orig,
                            'fixity': x['fixity'],
                            'kind': x['kind']
                        }, found_infix_ops))

                    if (FunUniq.INFIX, effective_id) not in ext_symbol_table.functions: # New name for infix op (note that we can only forbid duplicates after type normalisation)
                        ext_symbol_table.functions[(FunUniq.INFIX, effective_id)] = []

                    ext_symbol_table.functions[(FunUniq.INFIX, effective_id)].extend(add_entries)

                if not found_op_in_headerfile:
                    ERROR_HANDLER.addError(ERR.ImportOpIdentifierNotFound, [match_orig, modname, headerfiles[modname]['path']])
        
        for uq_type_id in unique_type_ids: # Type synonyms
            #print(uq_type_id)

            matching = list(filter(lambda x: x.name.val == uq_type_id, type_imports))
            #print(len(matching))
            if len(matching) > 1:
                ERROR_HANDLER.addWarning(WARN.DuplicateTypeSameModuleImport, [uq_type_id, modname, list(map(lambda x: x.name,matching))])

            if importall_present:
                found = cur_symbols['typesyns'][uq_type_id]

                if uq_type_id not in ext_symbol_table.type_syns: # New name
                    ext_symbol_table.type_syns[uq_type_id] = {
                        'def_type': found,
                        'module': modname,
                        'orig_id': uq_type_id
                    }
                else:
                    ERROR_HANDLER.addError(ERR.ClashImportType, [uq_type_id, importall_statement])

            for match in matching:
                #print("MATCH",match)
                match_orig = match.name.val
                effective_id = match.alias.val if match.alias is not None else match_orig

                if match_orig in cur_symbols['typesyns']:
                    found = cur_symbols['typesyns'][match_orig]

                    if effective_id not in ext_symbol_table.type_syns: # New name
                        ext_symbol_table.type_syns[effective_id] = {
                            'def_type': found,
                            'module': modname,
                            'orig_id': match_orig
                        }
                    else:
                        ERROR_HANDLER.addError(ERR.ClashImportType, [effective_id, match.name if match.alias is None else match.alias])
                else:
                    ERROR_HANDLER.addError(ERR.ImportTypeSynNotFound, [match_orig, modname, headerfiles[modname]['path']])

        #ERROR_HANDLER.checkpoint()

    return ext_symbol_table, unique_names
