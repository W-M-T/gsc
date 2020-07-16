#!/usr/bin/env python3

from lib.imports.imports import export_headers, import_headers, getImportFiles, getHeaders, getExternalSymbols, HEADER_EXT, SOURCE_EXT, IMPORT_DIR_ENV_VAR_NAME
from lib.analysis.error_handler import *
from lib.datastructure.AST import AST, FunKind, FunUniq, FunKindToUniq
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.position import Position
from lib.datastructure.symbol_table import SymbolTable, ExternalTable
from lib.datastructure.scope import NONGLOBALSCOPE

from lib.builtins.types import BUILTIN_TYPES, VOID_TYPE
from lib.builtins.functions import ENTRYPOINT_FUNCNAME
from lib.builtins.builtin_mod import enrichExternalTable, BUILTINS_NAME

from lib.util.util import treemap, selectiveApply, iterative_topological_sort

from lib.parser.parser import parseTokenStream
from lib.parser.lexer import tokenize
from lib.debug.AST_prettyprinter import print_node, subprint_type

import os
from enum import IntEnum
from collections import OrderedDict



'''
Replace all type synonyms in type with their definition, until the base case.
'''
def normalizeType(type_id, symbol_table, ext_table, err_produced=[], full_normalize=True):
    # Sadly we cannot just merge the typesyns in symbol_table and ext_table, because we need to overwrite them in each table and the pointers do not work out to accomplish that
    def replace_other(x):
        #print(x)
        if type(x.val) is Token:
            found_typesyn = x.val.val
            #print(found_typesyn,type_id)
            if type_id == found_typesyn:
                if type_id in symbol_table.type_syns:
                    ERROR_HANDLER.addError(ERR.CyclicTypeSyn, [type_id, symbol_table.type_syns[type_id]['decl']])
                else:
                    ERROR_HANDLER.addError(ERR.CyclicTypeSyn, [type_id, print_node(ext_table.type_syns[type_id]['def_type'])])
            else:
                print(ext_table)
                if found_typesyn in symbol_table.type_syns:
                    #print("Replacing {} in {}".format(found_typesyn, type_id))
                    #print("with def",symbol_table.type_syns[found_typesyn]['def_type'])
                    x.val = symbol_table.type_syns[found_typesyn]['def_type']
                elif found_typesyn in ext_table.type_syns: # other type was in external table
                    ERROR_HANDLER.addError(ERR.CyclicTypeSynExternal, [type_id, print_node(ext_table.type_syns[found_typesyn]['def_type'])])
                elif full_normalize:
                    if x not in err_produced:
                        err_produced.append(x)
                        ERROR_HANDLER.addError(ERR.UndefinedTypeId, [found_typesyn, x])
        return x

    if type_id in symbol_table.type_syns:
        def_type = symbol_table.type_syns[type_id]['def_type']
        symbol_table.type_syns[type_id]['def_type'] = treemap(def_type, lambda x: selectiveApply(AST.TYPE, x, replace_other), replace=True)
    else:
        def_type = ext_table.type_syns[type_id]['def_type']
        ext_table.type_syns[type_id]['def_type'] = treemap(def_type, lambda x: selectiveApply(AST.TYPE, x, replace_other), replace=True)
    #print("DEF_TYPE",def_type)





def getTypeDependencies(type_id, ext_table):
    def_type = ext_table.type_syns[type_id]['def_type']

    children = OrderedDict()
    def get_child(x):
        if type(x.val) is Token:
            found_typesyn = x.val.val
            if type_id == found_typesyn:
                print(type_id)
                '''
                if found_typesyn in symbol_table.type_syns:
                    ERROR_HANDLER.addError(ERR.CyclicTypeSyn, [type_id, symbol_table.type_syns[type_id]['decl']])
                else: # other type was in external table
                    ERROR_HANDLER.addError(ERR.CyclicTypeSynExternal, [type_id])
                '''
            else:
                if found_typesyn in ext_table.type_syns:
                    children[found_typesyn] = None

    treemap(def_type, lambda x: selectiveApply(AST.TYPE, x, get_child), replace=False)
    return list(children)

def resolveTypeDependency(type_entry, modname, own_typesyns, imported_typesyns):
    type_id = type_entry[0]
    typedef = type_entry[1]

    children = OrderedDict()
    def resolveChild(x):
        if type(x.val) is Token:
            found_typesyn = x.val.val
            if type_id == found_typesyn:
                #print("Cyclic",type_id)
                ERROR_HANDLER.addError(ERR.CyclicTypeSyn, [type_id, modname, "type {} = {}".format(type_id, print_node(typedef))])
            else: # Found a name to resolve
                #print("Found in def", type_id ,"was",found_typesyn)
                if found_typesyn in own_typesyns[modname]: # Local definition found, choose that
                    #print("FOUND LOCAL DEF")
                    x.val = AST.MOD_TYPE(module=modname, orig_id=found_typesyn)
                else:
                    flag_found = False
                    for other_mod, other_typesyns in imported_typesyns[modname].items():
                        #print(other_typesyns)
                        matches = list(filter(lambda x: x['effective_id'] == found_typesyn, other_typesyns))
                        if len(matches) > 0:
                            flag_found = True
                            x.val = AST.MOD_TYPE(module=other_mod, orig_id = matches[0]['orig_id'])
                            break
                    if not flag_found:
                        ERROR_HANDLER.addError(ERR.TypeIdNotFound, [found_typesyn, type_id, modname])
    treemap(typedef, lambda x: selectiveApply(AST.TYPE, x, resolveChild), replace=False)


# TODO give warning if local typesyn shadows imported one
def normalizeAllTypes(ast, symbol_table, ext_table, main_mod_name, full_normalize=True, headerfiles=[], typesyn_headerfiles=[]): # What a despicable function
    # Make an overview of the types in scope per module
    all_regular_modnames = list(OrderedDict.fromkeys(list(map(lambda x: x[1], ext_table.type_syns.keys())) + [main_mod_name] + list(headerfiles.keys())))
    all_recursive_modnames = list(OrderedDict.fromkeys(list(typesyn_headerfiles.keys())))

    all_modnames = list(OrderedDict.fromkeys(all_regular_modnames + all_recursive_modnames))

    #print(headerfiles)

    # Get list of all defined type syns per module
    own_defined_typesyns = OrderedDict()
    for modname in all_modnames:
        #print(modname)
        if modname in typesyn_headerfiles:
            # Own defined types from typesyn_headerfiles
            temp_me = list(typesyn_headerfiles[modname]["symbols"]["typesyns"].items())
            temp_me = OrderedDict(list(map(lambda x: (x[0], x[1]), temp_me))) # tuple of original id and type_def
            own_defined_typesyns[modname] = temp_me
        else:
            temp_me = OrderedDict(list(map(lambda y: (y[1]['orig_id'], y[1]['def_type']), filter(lambda x: x[0][1] == modname, ext_table.type_syns.items()))))
            own_defined_typesyns[modname] = temp_me
    

    # Get list of effective type syns per module + what their original id was
    my_typesyn_imports = OrderedDict()
    for modname in all_modnames:
        if modname == BUILTINS_NAME:
            my_typesyn_imports[modname] = {}

        elif modname == main_mod_name:
            my_typesyn_imports[modname] = {}
            #print("internal")
            all_imports = OrderedDict.fromkeys(map(lambda x: x.name.val, ast.imports))
            try:
                del all_imports[modname]
            except KeyError:
                pass
            all_imports = list(all_imports)
            for importname in all_imports:
                cur_imports = list(filter(lambda x: x.name.val == importname, ast.imports))

                importall_present = any(map(lambda x: x.importlist is None, cur_imports))

                all_cur_imports = [item for x in cur_imports if x.importlist is not None for item in x.importlist]
                all_type_imports = list(filter(lambda x: x.name.typ == TOKEN.TYPE_IDENTIFIER, all_cur_imports))

                type_import_list = []
                for import_statement in all_type_imports:
                    effective_id = import_statement.name.val if import_statement.alias is None else import_statement.alias.val
                    orig_id = import_statement.name.val
                    type_import_list.append({
                        'effective_id': effective_id,
                        'orig_id': orig_id
                    })
                #print(all_type_imports)
                my_typesyn_imports[modname][importname] = {
                    'importall': importall_present,
                    'type_imports': type_import_list
                }
            #print(my_typesyn_imports[modname])

        elif modname in all_regular_modnames:
            #print("regular",modname)
            my_typesyn_imports[modname] = headerfiles[modname]["symbols"]["depends"]
            #print(my_typesyn_imports[modname])

        else:
            #print("recursive",modname)
            my_typesyn_imports[modname] = typesyn_headerfiles[modname]["symbols"]["depends"]
           # print(my_typesyn_imports[modname])

    # Rewrite importall to specific names
    for source_modname, target_mod_dict in my_typesyn_imports.items():
        #print("Source",source_modname)
        #print("My own",own_defined_typesyns)
        for target_modname, target_info in target_mod_dict.items():
            #print("target",target_modname)
            #print(target_info['type_imports'])
            #print(target_info['importall'])

            if target_info['importall']:
                #print("SHOULD IMPORT ALL")
                extra_typesyns = list(map(lambda x: {
                    'effective_id': x[0],
                    'orig_id': x[0]
                }, own_defined_typesyns[target_modname].items()))
                target_info['type_imports'].extend(extra_typesyns)
                #print(own_defined_typesyns[target_modname])
            target_mod_dict[target_modname] = target_info['type_imports']
    '''
    #print(my_typesyn_imports)
    for k,v in my_typesyn_imports.items():
        #print("+",k)
        #print(v)
        pass
    '''
    # Resolve the types in typesyns
    for modname, type_entries in own_defined_typesyns.items():
        #print(modname)

        for type_entry in type_entries.items():
            resolveTypeDependency(type_entry, modname, own_defined_typesyns, my_typesyn_imports)
            print(type_entry)
    ERROR_HANDLER.checkpoint()

    # Get type syn dependencies and do topological sort:
    type_graph = {}
    for type_id, def_type in my_typesyn_imports.items():
        pass
        #type_graph[type_id] = getTypeDependencies(type_id, ext_table)
    exit()
    print("Type graph",type_graph)
    exit()
    topo = iterative_topological_sort(type_graph, list(ext_table.type_syns)[0])
    print(topo)
    ERROR_HANDLER.checkpoint()
    exit()

    err_produced = []
    for type_id in reversed(topo):
        normalizeType(type_id, symbol_table, ext_table, err_produced=err_produced, full_normalize=full_normalize)
    #TODO for exponential types this is still slow because after replacing, the entire subtree is traversed. This should not be necessary


    #print(type_graph)
    ERROR_HANDLER.checkpoint()
        


'''
Give an error for types containing Void in their input, or Void as a non-base type in the output
Also produce an error for undefined types (should probably be a separate function)
It is not necessary for types to be normalised yet, since type syns are checked for void before anything else
Also forbid multiple instances of main and require it to be of type "-> Int" (maybe should be a function called on the symbol table after normalisation?)
'''
def forbid_illegal_types(symbol_table, ext_table):
    # Require type syns to not contain Void
    for (type_id, modname), type_dict in ext_table.type_syns.items():
        if type_dict['decl'] is None:
            continue
        type_syn = type_dict['decl']
        #print(type_syn)
        #print("  a  ")
        def killVoidType(node):
            if type(node.val) is Token and node.val.val == VOID_TYPE:
                # Type syn has void in type
                ERROR_HANDLER.addError(ERR.TypeSynVoid, [type_id, node])
            return node

        treemap(type_syn, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require global vars to have a type and not contain Void
    for glob_var_id, glob_var in symbol_table.global_vars.items():

        if glob_var.type is None:
            # Global var has no type (we're doing type checking for now, not inference)
            ERROR_HANDLER.addError(ERR.GlobalVarTypeNone, [glob_var.id.val, glob_var])
        else:
            def killVoidType(node):
                if type(node.val) is Token and node.val.val == VOID_TYPE:
                    # Global variable type contains Void
                    ERROR_HANDLER.addError(ERR.GlobalVarVoid, [glob_var_id, node])
                return node
            treemap(glob_var.type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require function types to not be none, and to not have Void as an input type and no direct Void return Type
    for fun_list in symbol_table.functions.values():
        for fun in fun_list:
            if fun['type'] is None:
                # Function has no type
                ERROR_HANDLER.addError(ERR.FunctionTypeNone, [fun['def'].id.val, fun['def']])
            else:
                def killVoidType(node):
                    if type(node.val) is Token and node.val.val == VOID_TYPE:
                        # Function input type contains void
                        ERROR_HANDLER.addError(ERR.FunctionInputVoid, [fun['def'].id.val, node])
                    return node
                for from_type in fun['type'].from_types:
                    treemap(from_type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

                # Forbid non-direct Void return type
                returntype = fun['type'].to_type
                if not (type(returntype) is AST.TYPE and type(returntype.val) is Token and returntype.val.val == "Void"): # Not direct Void type
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == VOID_TYPE:
                            # Function output contains Void indirectly
                            ERROR_HANDLER.addError(ERR.FunctionOutputNestedVoid, [fun['def'].id.val, node])
                        return node
                    treemap(returntype, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

            # Go over local variable types
            for local_var in fun['local_vars'].values():
                if local_var.type is None:
                    # Local var has no type
                    ERROR_HANDLER.addError(ERR.LocalVarTypeNone, [local_var.id.val, fun['def'].id.val, local_var])
                else:
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == VOID_TYPE:
                            # Local var has void in type
                            ERROR_HANDLER.addError(ERR.LocalVarVoid, [local_var.id.val, fun['def'].id.val, node.val])
                        return node
                    treemap(local_var, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Check if main exists at most once, and with type "-> Int"
    if (FunUniq.FUNC, ENTRYPOINT_FUNCNAME) in symbol_table.functions:
        if len(symbol_table.functions[(FunUniq.FUNC, ENTRYPOINT_FUNCNAME)]) > 1:
            ERROR_HANDLER.addError(ERR.MultipleMain, [])
        for match in symbol_table.functions[(FunUniq.FUNC, ENTRYPOINT_FUNCNAME)]:
            temp_from_types = match['type'].from_types
            temp_to_type = match['type'].to_type
            if not (temp_from_types == [] and temp_to_type is not None and (type(temp_to_type.val) == AST.BASICTYPE and temp_to_type.val.type_id.val == "Int")):
                ERROR_HANDLER.addError(ERR.WrongMainType, [match['type']])

    ERROR_HANDLER.checkpoint()


def fixate_operator_properties(symbol_table, ext_table):
    op_keys = OrderedDict.fromkeys(list(filter(lambda x: x[0] == FunUniq.INFIX, list(symbol_table.functions.keys()) + list(ext_table.functions.keys()))))

    def getProp(func_entry):
        if "fixity" in func_entry.keys(): # External symbol
            return (func_entry["fixity"], func_entry["kind"])
        else: # Internal symbol
            return (func_entry["def"].fixity.val, func_entry["def"].kind)


    for (uq, op_id) in op_keys:
        #print(uq, op_id)
        cur_ops = symbol_table.functions.get((uq, op_id), []) + ext_table.functions.get((uq, op_id), [])

        #print(op_id)
        all_props = OrderedDict.fromkeys(list(map(getProp, cur_ops)))
        if len(all_props) > 1:
            prop_strings = map(lambda x: "{} {}".format(x[1].name.lower(), x[0]), all_props)
            ERROR_HANDLER.addError(ERR.MultipleOpIdPropertiesFound, [op_id, "\n".join(prop_strings)])
    #ERROR_HANDLER.checkpoint()

'''
Requires types to have been normalized
'''
def check_functype_clashes(symbol_table, ext_table):
    func_keys = OrderedDict.fromkeys(list(symbol_table.functions.keys()) + list(ext_table.functions.keys()))

    def getSourceMod(func_entry):
        if "module" in func_entry.keys(): # External symbol
            return func_entry["module"]
        else: # Internal symbol
            return None

    for (uq, f_id) in func_keys:
        #print(uq, f_id)
        error_pairs = []
        cur_funcs = list(enumerate(symbol_table.functions.get((uq, f_id), []) + ext_table.functions.get((uq, f_id), [])))

        for ix, func in cur_funcs:
            my_type = func['type']

            same_types = list(filter(lambda x: AST.equalVals(x[1]['type'], my_type), cur_funcs))
            for sam in same_types:
                if ix != sam[0]: # Other operator with same type
                    func_combo = sorted((ix,sam[0]))
                    if not func_combo in error_pairs: # Pair of functions with same type not seen yet
                        error_pairs.append(func_combo)

        for (a,b) in error_pairs:
            a_mod, b_mod = list(map(lambda x: getSourceMod(cur_funcs[x][1]), (a,b)))
            if a_mod is None and b_mod is None: # Two function defintions in this file with same type
                ERROR_HANDLER.addError(ERR.FuncTypeLocalClash, [f_id, uq.name, print_node(cur_funcs[a][1]['type']), cur_funcs[a][1]['def'].id, cur_funcs[b][1]['def'].id])

            if a_mod is not None and b_mod is not None: # Two imported function definition imports with same type
                if not any(map(lambda x: x == BUILTINS_NAME, [a_mod, b_mod])):
                    ERROR_HANDLER.addError(ERR.FuncTypeImportClash, [f_id, uq.name, print_node(cur_funcs[a][1]['type']), a_mod, b_mod])

            if a_mod == BUILTINS_NAME or b_mod == BUILTINS_NAME: # Function trying to shadow builtin
                you, you_mod = (a, a_mod) if b_mod == BUILTINS_NAME else (b, b_mod)
                if you_mod is None: # Internal
                    ERROR_HANDLER.addError(ERR.FuncTypeBuiltinShadow, [f_id, uq.name, print_node(cur_funcs[you][1]['type']), cur_funcs[you][1]['def'].id])
                else: # External
                    ERROR_HANDLER.addError(ERR.FuncTypeBuiltinShadowImport, [f_id, uq.name, print_node(cur_funcs[you][1]['type'])])

            if None in [a_mod, b_mod] and not all(map(lambda x: x is None, [a_mod, b_mod])): # Internal def shadowing import
                other = list(filter(lambda x: x is not None, [a_mod, b_mod]))[0]
                you = list(filter(lambda x: x[0] is None, [(a_mod,a), (b_mod,b)]))[0][1]
                if not any(map(lambda x: x == BUILTINS_NAME, [a_mod, b_mod])): # Not builtin
                    ERROR_HANDLER.addWarning(WARN.ShadowFuncIdType, [f_id, uq.name, other, print_node(cur_funcs[a][1]['type']), cur_funcs[you][1]['def'].id])

    #ERROR_HANDLER.checkpoint()

'''
Helper function for symbol table building
Return a dict with function info (insertion order is meaningful)
'''
def buildFuncEntry(val):
    temp_entry = {"type": val.type, "def": val}# "arg_vars": OrderedDict(), "local_vars":OrderedDict()}

    funarg_vars = OrderedDict()
    local_vars = OrderedDict()

    for ix, arg in enumerate(val.params):
        if not arg.val in funarg_vars:
            found_type = val.type.from_types[ix] if val.type is not None and ix in range(len(val.type.from_types)) else None
            funarg_vars[arg.val] = {"id":arg, "type":found_type}
        else:
            # Arg name was already used
            ERROR_HANDLER.addError(ERR.DuplicateArgName, [arg])
    for vardecl in val.vardecls:
        if vardecl.id.val in funarg_vars:
            # The local var id is already an arg id
            ERROR_HANDLER.addWarning(WARN.ShadowFunArg, [vardecl.id])
        if not vardecl.id.val in local_vars:
            local_vars[vardecl.id.val] = vardecl
        else:
            # The local var id was already used
            ERROR_HANDLER.addError(ERR.DuplicateVarDef, [vardecl.id, local_vars[vardecl.id.val].id])

    temp_entry["arg_vars"] = funarg_vars
    temp_entry["local_vars"]  = local_vars

    return temp_entry


def buildSymbolTable(ast, modname, just_for_headerfile=True, ext_symbol_table=None):
    symbol_table = SymbolTable()

    if ext_symbol_table is None: # If not running with imports, at least use builtins
        ext_symbol_table = enrichExternalTable(ExternalTable())
    '''
    print("Imports")
    for el in ast.imports:
        print(el)
    #'''
    #print("Decls")
    
    for decl in ast.decls:
        val = decl.val
        if type(val) is AST.VARDECL:
            #print("Var")
            var_id = val.id.val
            #print(var_id)
            if not var_id in symbol_table.global_vars: # New global var decl
                if not just_for_headerfile:
                    # Test if it exists in other module
                    if var_id in ext_symbol_table.global_vars:
                        # No need to check if it's builtin, since there are no builtin globals
                        ERROR_HANDLER.addWarning(WARN.ShadowGlobalOtherModule, [var_id, ext_symbol_table.global_vars[var_id]['module'], val.id])

                symbol_table.global_vars[var_id] = val
            else:
                # This global var identifier was already used
                ERROR_HANDLER.addError(ERR.DuplicateGlobalVarId, [val.id, symbol_table.global_vars[var_id].id])
            #print(print_node(val))

        elif type(val) is AST.FUNDECL:
            #print("Function")
            #print(val)
            #print(print_node(val))
            #print("params")
            #print(val.params)

            # Types are not normalised here yet, because we don't yet have all type syn
            uniq_kind = FunKindToUniq(val.kind)

            # Test if argument count and type count match
            if val.type is not None:
                from_types = val.type.from_types
                if len(from_types) != len(val.params):
                    # Arg count doesn't match input type
                    ERROR_HANDLER.addError(ERR.ArgCountDoesNotMatchSign, [val.id])

            # No check for external/builtin shadowing. Happens during type normalization
            # Test if this function is already defined
            fun_id = val.id.val
            if not (uniq_kind, fun_id) in symbol_table.functions:

                # Completely new name
                symbol_table.functions[(uniq_kind,fun_id)] = []

                temp_entry = buildFuncEntry(val)
                #print(temp_entry["arg_vars"]) # TODO we do not as of yet test that all uses of types were defined

                symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

            else: # Already defined in the table, check for overloading
                temp_entry = buildFuncEntry(val)
                symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

        elif type(val) is AST.TYPESYN:
            #print("Type")
            type_id = val.type_id.val
            def_type = val.def_type



            if (type_id, BUILTINS_NAME) in ext_symbol_table.type_syns:
                    # Type identifier is reserved (builtin typesyn)
                    ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])
            elif type_id in BUILTIN_TYPES:
                # Type identifier is reserved (basic type)
                ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])
            elif (type_id, modname) in ext_symbol_table.type_syns:
                # Type identifier already used
                ERROR_HANDLER.addError(ERR.DuplicateTypeId, [val.type_id, ext_symbol_table.type_syns[(val.type_id.val, modname)]['decl']])
            else:
                ext_symbol_table.type_syns[(type_id, modname)] = OrderedDict([
                    ("def_type", def_type),
                    ("orig_id", type_id),
                    ("decl", val),
                ])

    ERROR_HANDLER.checkpoint()

    #print("--------------------------")
    #print(symbol_table.repr_short())
    return symbol_table, ext_symbol_table


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(symbol_table, ext_table):
    # Resolve names used in expressions in global variable definitions:
    # Order matters here as to what is in scope

    # Globals
    for glob_var_id, glob_var in symbol_table.global_vars.items():
        in_scope = list(map(lambda x: x[0], filter(lambda x: list(symbol_table.global_vars.keys()).index(glob_var_id) > list(symbol_table.global_vars.keys()).index(x[0]), symbol_table.global_vars.items())))
        glob_var.expr = resolveExprNames(glob_var.expr, symbol_table, ext_table, glob=True, in_scope_globals=in_scope)

    # Functions
    in_scope_globals = list(symbol_table.global_vars.keys())
    for f in symbol_table.functions: # Functions
        for i in range(0, len(symbol_table.functions[f])): # Overloaded functions
            in_scope_locals = {'locals': [], 'args': list(map(lambda x: x[0], symbol_table.functions[f][i]['arg_vars'].items()))}
            for v in symbol_table.functions[f][i]['def'].vardecls:
                in_scope = list(map(lambda x: x[0], filter(
                    lambda x: list(symbol_table.functions[f][i]['local_vars'].keys()).index(v.id.val) > list(symbol_table.functions[f][i]['local_vars'].keys()).index(x[0]),
                    symbol_table.functions[f][i]['local_vars'].items())))

                in_scope_locals['locals'] = in_scope
                resolveExprNames(v.expr, symbol_table, ext_table, False, in_scope_globals, in_scope_locals)

            in_scope_locals['locals'] = list(symbol_table.functions[f][i]['local_vars'].keys())

            # Expressions and assignments
            treemap(symbol_table.functions[f][i]['def'].stmts, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: resolveExprNames(y, symbol_table, ext_table, False, in_scope_globals, in_scope_locals)))
            treemap(symbol_table.functions[f][i]['def'].stmts, lambda node: selectiveApply(AST.ASSIGNMENT, node, lambda y: resolveAssignName(y, symbol_table, ext_table, in_scope_globals, in_scope_locals)))

'''
Funcall naar module, (FunUniq, id) (nog geen type)
Varref naar module, scope (global of local + naam of arg + naam)
Type-token naar module, naam of forall type
'''

def resolveAssignName(assignment, symbol_table, ext_table, in_scope_globals=[], in_scope_locals={}):
    scope = None
    module = None
    if assignment.varref.id.val in in_scope_locals['locals']:
        scope = NONGLOBALSCOPE.LocalVar
    elif assignment.varref.id.val in in_scope_locals['args']:
        scope = NONGLOBALSCOPE.ArgVar
    elif assignment.varref.id.val in in_scope_globals:
        scope = None
    elif assignment.varref.id.val in ext_table.global_vars:
        scope = None
        module = ext_table.global_vars[assignment.varref.id.val]['module']
    else:
        ERROR_HANDLER.addError(ERR.UndefinedVar, [assignment.varref.id.val, assignment.varref])
        return assignment

    pos = assignment.varref._start_pos
    if scope is not None:
        assignment.varref = AST.RES_VARREF(val=AST.RES_NONGLOBAL(
            scope=scope,
            id=assignment.varref.id,
            fields=assignment.varref.fields
        ))
    else:
        assignment.varref = AST.RES_VARREF(val=AST.RES_GLOBAL(
            module=module,
            id=assignment.varref.id,
            fields=assignment.varref.fields
        ))
    assignment.varref._start_pos = pos

    return assignment

# TODO: Really check if all expression types are handled correctly here.
# TODO: Fix bug where you get multiple errors for variable undefined when using nested functions.
'''
Resolve an expression with the following globals in scope
Functions are always in scope
'''
def resolveExprNames(expr, symbol_table, ext_table, glob=False, in_scope_globals=[], in_scope_locals={}):
    for i in range(0, len(expr.contents)):
        if type(expr.contents[i]) is AST.VARREF:
            if glob:
                # TODO: Disallow imported globals
                if expr.contents[i].id.val not in in_scope_globals:
                    ERROR_HANDLER.addError(ERR.UndefinedGlobalVar, [expr.contents[i].id.val, expr.contents[i]])
                    break
                # TODO: Not hardcode this, it should depend on the module.
                pos = expr.contents[i]._start_pos
                expr.contents[i] = AST.RES_VARREF(val=AST.RES_GLOBAL(
                    module=None,
                    id=expr.contents[i].id,
                    fields=expr.contents[i].fields
                ))
                expr.contents[i]._start_pos = pos
            else:
                scope = None
                module = None
                if expr.contents[i].id.val in in_scope_locals['locals']:
                    scope = NONGLOBALSCOPE.LocalVar
                elif expr.contents[i].id.val in in_scope_locals['args']:
                    scope = NONGLOBALSCOPE.ArgVar
                elif expr.contents[i].id.val in in_scope_globals:
                    scope = None
                elif expr.contents[i].id.val in ext_table.global_vars:
                    scope = None
                    module = ext_table.global_vars[expr.contents[i].id.val]['module']
                else:
                    ERROR_HANDLER.addError(ERR.UndefinedVar, [expr.contents[i].id.val, expr.contents[i]])
                    break

                pos = expr.contents[i]._start_pos
                if scope is not None:
                    expr.contents[i] = AST.RES_VARREF(val=AST.RES_NONGLOBAL(
                        scope=scope,
                        id=expr.contents[i].id,
                        fields=expr.contents[i].fields
                    ))
                else:
                    expr.contents[i] = AST.RES_VARREF(val=AST.RES_GLOBAL(
                        module=module,
                        id=expr.contents[i].id,
                        fields=expr.contents[i].fields
                    ))
                expr.contents[i]._start_pos = pos
        elif type(expr.contents[i]) is AST.TUPLE:
            expr.contents[i].a = resolveExprNames(expr.contents[i].a, symbol_table, ext_table, glob, in_scope_globals, in_scope_locals)
            expr.contents[i].b = resolveExprNames(expr.contents[i].b, symbol_table, ext_table, glob, in_scope_globals, in_scope_locals)
        elif type(expr.contents[i]) is AST.FUNCALL:
            for k in range(0, len(expr.contents[i].args)):
                expr.contents[i].args[k] = resolveExprNames(expr.contents[i].args[k], symbol_table, ext_table, glob, in_scope_globals, in_scope_locals)

    return expr

''' Parse expression atoms (literals, identifiers, func call, subexpressions, prefixes) '''
def parseAtom(exp, symbol_table, ext_table, exp_index):

    if type(exp[exp_index]) is AST.RES_VARREF or type(exp[exp_index]) is Token or type(exp[exp_index]) is AST.TUPLE: # Literal / identifier
        res = exp[exp_index]
        # TODO: This was without AST ParsedExpr, possibly remove this again
        return res, exp_index + 1
    elif type(exp[exp_index]) is AST.DEFERREDEXPR: # Sub expression
        sub_expr, _ = parseExpression(exp[exp_index].contents, symbol_table, ext_table)
        return AST.PARSEDEXPR(val=sub_expr), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == FunKind.PREFIX: # Prefix
        if (FunUniq.PREFIX, exp[exp_index].id.val) not in ext_table.functions and (FunUniq.PREFIX, exp[exp_index].id.val) not in symbol_table.functions:
            ERROR_HANDLER.addError(ERR.UndefinedPrefixOp, [exp[exp_index].id.val, exp[exp_index]])
        prefix = exp[exp_index]
        sub_expr, _ = parseExpression(prefix.args, symbol_table, ext_table)
        return AST.FUNCALL(id=prefix.id, kind=2, args=[sub_expr]), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == FunKind.FUNC: # Function call
        func_args = []
        funcall = exp[exp_index]
        if funcall.args is not None:
            for arg in funcall.args:
                sub_expr, _ = parseExpression(arg.contents, symbol_table, ext_table)
                func_args.append(sub_expr)
        return AST.FUNCALL(id=funcall.id, kind=1, args=func_args), exp_index + 1
    else:
        raise Exception("Unexpected token encountered while parsing atomic value in expression.")

# TODO: Add custom operators
''' Parse expressions by performing precedence climbing algorithm. '''
def parseExpression(exp, symbol_table, ext_table, min_precedence = 1, exp_index = 0):
    result, exp_index = parseAtom(exp, symbol_table, ext_table, exp_index)

    while True:
        if exp_index < len(exp) and ((FunUniq.INFIX, exp[exp_index].val) not in ext_table.functions and (FunUniq.INFIX, exp[exp_index].val) not in symbol_table.functions):
            ERROR_HANDLER.addError(ERR.UndefinedOp, [exp[exp_index]])
            break
        elif exp_index >= len(exp):
            break
        elif (FunUniq.INFIX, exp[exp_index].val) in ext_table.functions and ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity'] < min_precedence:
            break
        elif (FunUniq.INFIX, exp[exp_index].val) in symbol_table.functions and symbol_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['def'].fixity.val < min_precedence:
            break

        if (FunUniq.INFIX, exp[exp_index].val) in ext_table.functions:
            if ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['kind'] == FunKind.INFIXL:
                next_min_prec = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity'] + 1
            else:
                next_min_prec = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity']
            kind = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['kind']
        else:
            if symbol_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['def'].kind == FunKind.INFIXL:
                next_min_prec = symbol_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['def'].fixity.val + 1
            else:
                next_min_prec = symbol_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['def'].fixity.val
            kind = symbol_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['def'].kind
        op = exp[exp_index]
        exp_index += 1
        rh_expr, exp_index = parseExpression(exp, symbol_table, ext_table, next_min_prec, exp_index)
        result = AST.FUNCALL(id=op, kind=kind, args=[result, rh_expr])

    return result, exp_index

''' Given the operator table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, symbol_table, ext_table):
    decorated_ast = treemap(ast,
                        lambda node:
                            selectiveApply(AST.DEFERREDEXPR, node,
                                lambda y:  parseExpression(y.contents, symbol_table, ext_table)[0]
                            )
                        )

    return decorated_ast

'''
Goal of this function is:
- To check for dead code after break/continue statements;
- To check for dead code after return statements;
- To check for break/continue statements outside of loops;
- To check that all paths return if the function should return something
'''
def analyseFuncStmts(func, statements, loop_depth=0, cond_depth=0):
    returns = False
    return_exp = not AST.equalVals(func.type.to_type, AST.TYPE(val=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Void")))

    for k in range(0, len(statements)):
        stmt = statements[k].val

        if type(stmt) is AST.IFELSE:
            returning_branches = 0
            # Check for each branch if it returns, count those branches
            for branch in stmt.condbranches:
                branch_return = analyseFuncStmts(func, branch.stmts, loop_depth, cond_depth + 1)
                returning_branches += branch_return

            # All of the branches return
            if returning_branches == len(stmt.condbranches):
                # Check if last branch is else (not elif)
                if stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    returns = True
                else: # Its an elif, since we do not know if the entire domain is covered we still expect a return
                    returns = False
                # Check for statements after the IFELSE statement (deadcode since all branches return)
                if k != len(statements) - 1 and stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    ERROR_HANDLER.addWarning(WARN.UnreachableStmtBranches, [statements[k+1]])

        elif type(stmt) is AST.LOOP:
            # Whether something inside a loop returns does not matter, since we cant assume anything about its condition
            _ = analyseFuncStmts(func, stmt.stmts, loop_depth + 1, cond_depth)
        elif type(stmt) is AST.BREAK or type(stmt) is AST.CONTINUE:
            # Check if break or continue while not in a loop
            if loop_depth == 0:
                ERROR_HANDLER.addError(ERR.BreakOutsideLoop, [stmt])
            else:
                # Check for statements after break or continue
                if k != len(statements) - 1:
                    ERROR_HANDLER.addWarning(WARN.UnreachableStmtContBreak, [statements[k + 1]])
        elif type(stmt) is AST.RETURN:
            # Check for statements after return
            if k != len(statements) - 1:
                ERROR_HANDLER.addWarning(WARN.UnreachableStmtReturn, [statements[k+1]])
            # We can return immediately here since all stmts after is considered deadcode.
            return True

    # We are at the top level and we still expect a return, so a return stmt is missing
    if not returns and return_exp and cond_depth == 0 and loop_depth == 0:
        ERROR_HANDLER.addError(ERR.NotAllPathsReturn, [func.id.val, func.id])

    return returns

'''Given the symbol table, find dead code statements after return/break/continue and see if all paths return'''
def analyseFunc(symbol_table):
    for (uniq, fun_id), decl_list in symbol_table.functions.items():
        for fundecl in decl_list:
            analyseFuncStmts(fundecl['def'], fundecl['def'].stmts)
    ERROR_HANDLER.checkpoint()

'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports
'''
'''
def analyse(ast, filename):
    return ast
    #file_mappings = resolveImports(ast, filename)
    #exit()
    symbol_table = buildSymbolTable(ast)
    forbid_illegal_types(symbol_table)
    normalizeAllTypes(symbol_table)

    #ast = resolveNames(ast, symbol_table)
    ast = fixExpression(ast, symbol_table)
'''

if __name__ == "__main__":
    from argparse import ArgumentParser
    argparser = ArgumentParser(description="SPL Semantic Analysis")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import libraries from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated library_name:path mapping list, to explicitly specify import paths", type=str)
    argparser.add_argument("-H", help="Produce a header file instead of an executable", action="store_true")
    args = argparser.parse_args()

    import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
    if not (all(map(lambda x: len(x)==2, import_mapping)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), import_mapping))):
        print("Invalid import mapping")
        exit()
    #print(import_mapping)
    import_mapping = {a:os.path.splitext(b)[0] for (a,b) in import_mapping}
    print("Import map:",import_mapping)

    if not args.infile.endswith(SOURCE_EXT):
        print("Input file needs to be {}".format(SOURCE_EXT))
        exit()

    main_mod_path = os.path.splitext(args.infile)[0]
    main_mod_name = os.path.basename(main_mod_path)

    compiler_target = {
        'header' : args.H,
        'object' : not args.H
    }

    with open(args.infile, "r") as infile:
        '''
        print(args.infile)
        print(args.lp)
        print(os.path.realpath(args.infile))
        print(os.path.dirname(os.path.realpath(args.infile)))
        '''

        from io import StringIO
        testprog = StringIO('''
//var illegal = 2;
Int pi = 3;
String aa = 2;
type Chara = Int
//type Void = Int
type String = [Char]
type OtherInt = Int
type TotallyNotChar = Char
type OtherListInt = [OtherInt]
type StringList = [(([String], Int), Chara)]
infixl 7 % (a, b) :: OtherInt [Bool] -> OtherListInt {
    OtherInt result = a;
    Int a = 2;
    while(result > b) {
        result = result - b;
    }
    return result;
}
infixl 7 % (a, b) :: Char Bool -> OtherListInt {
    OtherInt result = a;
    Int a = 2;
    while(result > b) {
        result = result - b;
    }
    return result;
}
f (x) :: Char -> Void {
    Int x2 = x;
    Int x = 2;
    return x;
}
f (x) :: Bool -> Int {
    Int x2 = x;
    Int x = 2;
    return x;
}
f (x) :: Int -> Int {
    Int x2 = x;
    Int x = 2;
    return x;
}
//*/
/*
g (x) {
    return 2;
}//*/
''')
        if False: # Debug
            tokenstream = tokenize(testprog)

            x = parseTokenStream(tokenstream, testprog)
            ERROR_HANDLER.setSourceMapping(testprog)
        else:
            tokenstream = tokenize(infile)

            x = parseTokenStream(tokenstream, infile)
            ERROR_HANDLER.setSourceMapping(infile)

        #ERROR_HANDLER.debug = True
        #ERROR_HANDLER.hidewarn = True
        #print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        #file_mappings = resolveImports(x, args.infile, import_mapping, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        #print(ERROR_HANDLER)

        if compiler_target['object']: # We need to actually read the headerfiles of the imports:
            headerfiles, typesyn_headerfiles = getHeaders(x,
                main_mod_name,
                HEADER_EXT,
                os.path.dirname(args.infile),
                file_mapping_arg=import_mapping,
                lib_dir_path=args.lp,
                lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
            # Get all external symbols
            external_symbol_table, all_import_modnames = getExternalSymbols(x, headerfiles, typesyn_headerfiles)
            external_symbol_table = enrichExternalTable(external_symbol_table)
            ERROR_HANDLER.checkpoint()

            symbol_table = buildSymbolTable(x, compiler_target['header'], ext_symbol_table=external_symbol_table)
            print(symbol_table)
            #print(all_import_modnames)
            print(external_symbol_table)
            normalizeAllTypes(symbol_table, external_symbol_table, full_normalize=True)
            #forbid_illegal_types(symbol_table)
            #analyseFunc(symbol_table)

            exit()
        else:
            symbol_table = buildSymbolTable(x, compiler_target['header'])
            print(symbol_table)
            normalizeAllTypes(symbol_table, enrichExternalTable(ExternalTable()), full_normalize=False)
            #print(symbol_table)
            exit()
            #forbid_illegal_types(symbol_table)
            #analyseFunc(symbol_table)
            #normalizeAllTypes(symbol_table)

            header_json = export_headers(symbol_table)

            outfile_name = os.path.splitext(args.infile)[0] + HEADER_EXT

            try:
                with open(outfile_name,"w") as outfile:
                    outfile.write(header_json)
                    print("Succesfully written headerfile",outfile_name)
            except Exception as e:
                print("{}: {}".format(e.__class__.__name__,str(e)))
            exit()


        '''
        import_headers(export_headers(symbol_table))
        exit()
        forbid_illegal_types(symbol_table)
        exit()
        print("NORMALIZING TYPES ==================")
        normalizeAllTypes(symbol_table)
        print(symbol_table)
        print("RESOLVING NAMES ====================")
        resolveNames(symbol_table)
        exit()
        analyse(x, args.infile)
        '''

        print("DONE")