#!/usr/bin/env python3

from lib.imports.imports import export_headers, import_headers, getImportFiles, getExternalSymbols, HEADER_EXT, SOURCE_EXT, IMPORT_DIR_ENV_VAR_NAME
from lib.analysis.error_handler import *
from lib.datastructure.AST import AST, FunKind, FunUniq, FunKindToUniq
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.symbol_table import SymbolTable, ExternalTable
from lib.datastructure.scope import NONGLOBALSCOPE

from lib.builtins.types import BUILTIN_TYPES, VOID_TYPE
from lib.builtins.functions import ENTRYPOINT_FUNCNAME
from lib.builtins.builtin_mod import enrichExternalTable, BUILTINS_NAME

from lib.util.util import treemap, selectiveApply

from lib.parser.parser import parseTokenStream
from lib.parser.lexer import tokenize
from lib.debug.AST_prettyprinter import print_node, subprint_type

import os
from enum import IntEnum
from collections import OrderedDict


'''
W.r.t. name resolution:
there's globals, locals and function parameters
'''

'''
Replace all type synonyms in type with their definition, until the base case.
Circularity is no concern because that is caught in the name resolution step for type synonyms.
We prevent pointer problems by rewriting type syns directly when they are added to to the symbol table
This also means that we should never need to recurse after rewriting a type syn once, because the rewrite result should already be normalized.
'''
def normalizeType(inputtype, symbol_table): # TODO add proper error handling
    if type(inputtype) is AST.TYPE:
        inputtype.val = normalizeType(inputtype.val, symbol_table)
        if type(inputtype.val) is AST.TYPE: # Unwrap so we don't have double occurrences of TYPE nodes
            return inputtype.val
        else:
            return inputtype
    if type(inputtype) is AST.BASICTYPE:
        return inputtype
    elif type(inputtype) is AST.TUPLETYPE:
        inputtype.a = normalizeType(inputtype.a, symbol_table)
        inputtype.b = normalizeType(inputtype.b, symbol_table)
        return inputtype
    elif type(inputtype) is AST.LISTTYPE:
        inputtype.type = normalizeType(inputtype.type, symbol_table)
        return inputtype
    elif type(inputtype) is AST.FUNTYPE:
        inputtype.from_types = list(map(lambda x: normalizeType(x, symbol_table), inputtype.from_types))
        inputtype.to_type = normalizeType(inputtype.to_type, symbol_table)
        return inputtype
    elif type(inputtype) is Token: # TODO If we decide to implement polymorphism, if it is not found here it, is a forall type
        if inputtype.val in symbol_table.type_syns:
            normalized_type = symbol_table.type_syns[inputtype.val]
            return normalized_type
        elif inputtype.val == VOID_TYPE:
            return inputtype
        else:
            print("[ERROR] Typename {} not defined!".format(inputtype.val))
            exit()
    else:
        print("Case not captured:",inputtype)
        exit()

def normalizeAllTypes(symbol_table): # TODO clean this up and add proper error handling
    # Normalize type syn definitions:
    # Not necessary because this is done during the creation of the symbol table, in order to require sequentiality

    # Normalize global var types
    for glob_var in symbol_table.global_vars.items():
        glob_var[1].type = normalizeType(glob_var[1].type, symbol_table)

    # Normalize function types and find duplicates
    flag = False # Handle this in the error handler
    for key, func_list in symbol_table.functions.items():
        found_typesigs = []
        #print(len(func_list))
        for func in func_list:
            func['type'] = normalizeType(func['type'], symbol_table)
            found_typesigs.append((func['type'], func))

        # Test if multiple functions have the same (normalized) type
        
        while len(found_typesigs) > 0:
            cur = found_typesigs.pop()

            find_match = [x for x in found_typesigs if AST.equalVals(x[0],cur[0])]
            if find_match: # TODO error handler collect + have it show it in order
                flag = True
                print('[ERROR] Overloaded function "{}" has multiple definitions with the same type:'.format(key[1]))
                print(cur[1]["def"].id)
                for el in find_match:
                    print(el[1]["def"].id)
                    found_typesigs.remove(el)

    if flag:
        exit()

    # Normalize local vars and args (should prolly do this in the first iteration on this, i.e. higher in this function)
    for key, func_list in symbol_table.functions.items():
        #print(len(func_list))
        for func in func_list:
            #print("FUNCTION LOCAL VARS OF", func['def'].id.val)
            for local_var_key, local_var in func['local_vars'].items():
                local_var.type = normalizeType(local_var.type, symbol_table)
            #print("FUNCTION ARG VARS OF", func['def'].id.val)
            # As a result of already normalising the type of the function signature, the types of arguments should already be normalised. (because of the magic of pointers!)
            #print(func['arg_vars'])

'''
Give an error for types containing Void in their input, or Void as a non-base type in the output
Also produce an error for undefined types (should probably be a separate function)
It is not necessary for types to be normalised yet, since type syns are checked for void before anything else
Also forbid multiple instances of main and require it to be of type "-> Int" (maybe should be a function called on the symbol table after normalisation?)
'''
def forbid_illegal_types(symbol_table):
    # Require type syns to not contain Void
    for type_id, type_syn in symbol_table.type_syns.items():
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
            if not (temp_from_types == [] and temp_to_type is not None and type(temp_to_type.val) == AST.BASICTYPE and temp_to_type.val.type_id.val == "Int"):
                ERROR_HANDLER.addError(ERR.WrongMainType, [match['type']])

    ERROR_HANDLER.checkpoint()

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


#TODO: We don't check for redefinition attempts of builtin functions or ops -> Do this in type normaliser
#TODO: Check if a main with signature -> Int was defined.

def buildSymbolTable(ast, just_for_headerfile=True, ext_symbol_table=None):
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
                        ERROR_HANDLER.addWarning(WARN.ShadowGlobalOtherModule, [var_id, ext_symbol_table.global_vars[var_id]['module']])

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

            if type_id in ext_symbol_table.type_syns:
                if ext_symbol_table.type_syns[type_id]['module'] == BUILTINS_NAME:
                    # Type identifier is reserved (builtin typesyn)
                    ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])
            elif type_id in BUILTIN_TYPES:
                # Type identifier is reserved (basic type)
                ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])


            if not type_id in symbol_table.type_syns:
                if not just_for_headerfile:
                    # Test if it exists in another module
                    if type_id in ext_symbol_table.type_syns:
                        if ext_symbol_table.type_syns[type_id]['module'] != BUILTINS_NAME:
                            # External type identifier is shadowed
                            ERROR_HANDLER.addWarning(WARN.ShadowTypeOtherModule, [type_id, ext_symbol_table.type_syns[type_id]['module']])

                normalized_type = normalizeType(def_type, symbol_table) # TODO dit gaat nog niet goed
                symbol_table.type_syns[type_id] = normalized_type
            else:
                # Type identifier already used
                ERROR_HANDLER.addError(ERR.DuplicateTypeId, [val.type_id, symbol_table.type_syns[val.type_id.val]])

    ERROR_HANDLER.checkpoint()

    #print("--------------------------")
    #print(symbol_table.repr_short())
    return symbol_table


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(symbol_table):
    # Resolve names used in expressions in global variable definitions:
    # Order matters here as to what is in scope

    # Globals
    for glob_var_id, glob_var in symbol_table.global_vars.items():
        in_scope = list(map(lambda x: x[0], filter(lambda x: list(symbol_table.global_vars.keys()).index(glob_var_id) > list(symbol_table.global_vars.keys()).index(x[0]), symbol_table.global_vars.items())))
        glob_var.expr = resolveExprNames(glob_var.expr, symbol_table, glob=True, in_scope_globals=in_scope)

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
                resolveExprNames(v.expr, symbol_table, False, in_scope_globals, in_scope_locals)

            in_scope_locals['locals'] = list(symbol_table.functions[f][i]['local_vars'].keys())

            # Expressions and assignments
            treemap(symbol_table.functions[f][i]['def'].stmts, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: resolveExprNames(y, symbol_table, False, in_scope_globals, in_scope_locals)))
            treemap(symbol_table.functions[f][i]['def'].stmts, lambda node: selectiveApply(AST.ASSIGNMENT, node, lambda y: resolveAssignName(y, symbol_table, in_scope_globals, in_scope_locals)))

'''
Funcall naar module, (FunUniq, id) (nog geen type)
Varref naar module, scope (global of local + naam of arg + naam)
Type-token naar module, naam of forall type
'''

def resolveAssignName(assignment, symbol_table, in_scope_globals=[], in_scope_locals={}):
    scope = None
    if assignment.varref.id.val in in_scope_locals['locals']:
        scope = NONGLOBALSCOPE.LocalVar
    elif assignment.varref.id.val in in_scope_locals['args']:
        scope = NONGLOBALSCOPE.ArgVar
    elif assignment.varref.id.val in in_scope_globals:
        scope = None
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
            module=None,
            id=assignment.varref.id,
            fields=assignment.varref.fields
        ))
    assignment.varref._start_pos = pos

    return assignment

# TODO: Really check if all expression types are handled correctly here.
'''
Resolve an expression with the following globals in scope
Functions are always in scope
'''
def resolveExprNames(expr, symbol_table, glob=False, in_scope_globals=[], in_scope_locals={}):
    for i in range(0, len(expr.contents)):
        if type(expr.contents[i]) is AST.VARREF:
            if glob:
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
                if expr.contents[i].id.val in in_scope_locals['locals']:
                    scope = NONGLOBALSCOPE.LocalVar
                elif expr.contents[i].id.val in in_scope_locals['args']:
                    scope = NONGLOBALSCOPE.ArgVar
                elif expr.contents[i].id.val in in_scope_globals:
                    scope = None
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
                        module=None,
                        id=expr.contents[i].id,
                        fields=expr.contents[i].fields
                    ))
                expr.contents[i]._start_pos = pos
        elif type(expr.contents[i]) is AST.TUPLE:
            expr.contents[i].a = resolveExprNames(expr.contents[i].a, symbol_table, glob, in_scope_globals, in_scope_locals)
            expr.contents[i].b = resolveExprNames(expr.contents[i].b, symbol_table, glob, in_scope_globals, in_scope_locals)
        elif type(expr.contents[i]) is AST.FUNCALL:
            for k in range(0, len(expr.contents[i].args)):
                expr.contents[i].args[k] = resolveExprNames(expr.contents[i].args[k], symbol_table, glob, in_scope_globals, in_scope_locals)

    return expr

''' Parse expression atoms (literals, identifiers, func call, subexpressions, prefixes) '''
def parseAtom(exp, ext_table, exp_index):

    if type(exp[exp_index]) is AST.RES_VARREF or type(exp[exp_index]) is Token or type(exp[exp_index]) is AST.TUPLE: # Literal / identifier
        res = exp[exp_index]
        return AST.PARSEDEXPR(val=res), exp_index + 1
    elif type(exp[exp_index]) is AST.DEFERREDEXPR: # Sub expression
        sub_expr, _ = parseExpression(exp[exp_index].contents, ext_table)
        return AST.PARSEDEXPR(val=sub_expr), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == FunKind.PREFIX: # Prefix
        if (FunUniq.PREFIX, exp[exp_index].id.val) not in ext_table.functions:
            ERROR_HANDLER.addError(ERR.UndefinedPrefixOp, [exp[exp_index].id.val, exp[exp_index]])
        prefix = exp[exp_index]
        sub_expr, _ = parseExpression(prefix.args, ext_table)
        return AST.FUNCALL(id=prefix.id, kind=2, args=[sub_expr]), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == FunKind.FUNC: # Function call
        func_args = []
        funcall = exp[exp_index]
        if funcall.args is not None:
            for arg in funcall.args:
                sub_expr, _ = parseExpression(arg.contents, ext_table)
                func_args.append(sub_expr)
        return AST.FUNCALL(id=funcall.id, kind=1, args=func_args), exp_index + 1
    else:
        raise Exception("Unexpected token encountered while parsing atomic value in expression.")

# TODO: Add custom operators
''' Parse expressions by performing precedence climbing algorithm. '''
def parseExpression(exp, ext_table, min_precedence = 1, exp_index = 0):
    result, exp_index = parseAtom(exp, ext_table, exp_index)

    while True:
        if exp_index < len(exp) and (FunUniq.INFIX, exp[exp_index].val) not in ext_table.functions:
            ERROR_HANDLER.addError(ERR.UndefinedOp, [exp[exp_index]])
            break
        elif exp_index >= len(exp) or ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity'] < min_precedence:
            break

        if ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['kind'] == FunKind.INFIXL:
            next_min_prec = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity'] + 1
        else:
            next_min_prec = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['fixity']
        kind = ext_table.functions[(FunUniq.INFIX, exp[exp_index].val)][0]['kind']
        op = exp[exp_index]
        exp_index += 1
        rh_expr, exp_index = parseExpression(exp, ext_table, next_min_prec, exp_index)
        result = AST.FUNCALL(id=op, kind=kind, args=[result, rh_expr])

    return result, exp_index

''' Given the operator table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, op_table):
    decorated_ast = treemap(ast,
                        lambda node:
                            selectiveApply(AST.DEFERREDEXPR, node,
                                lambda y:  AST.PARSEDEXPR(val=parseExpression(y.contents, op_table)[0])
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
    return_exp = False
    for k in range(0, len(statements)):
        stmt = statements[k].val
        if type(stmt) is AST.IFELSE:
            return_ctr = 0
            for branch in stmt.condbranches:
                does_return, rexp = analyseFuncStmts(func, branch.stmts, loop_depth, cond_depth + 1)
                return_exp = return_exp or rexp
                return_ctr += does_return

            if return_ctr == len(stmt.condbranches):
                if k is not len(statements) - 1 and stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    ERROR_HANDLER.addWarning(WARN.UnreachableStmtBranches, [statements[k+1]])
                if stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    return_exp = False
                else:
                    return_exp = True
                returns = True
            elif return_ctr > 0 and return_ctr < len(stmt.condbranches):
                return_exp = True

        elif type(stmt) is AST.LOOP:
            returns, return_exp = analyseFuncStmts(func, stmt.stmts, loop_depth + 1, cond_depth)
            if return_exp:
                returns = False
        elif type(stmt) is AST.BREAK or type(stmt) is AST.CONTINUE:
            if loop_depth == 0:
                ERROR_HANDLER.addError(ERR.BreakOutsideLoop, [stmt.val])
            else:
                if k is not len(statements) - 1:
                    ERROR_HANDLER.addWarning(WARN.UnreachableStmtContBreak, [statements[k + 1]])
                    return False, return_exp
        elif type(stmt) is AST.RETURN:
            if k is not len(statements) - 1:
                ERROR_HANDLER.addWarning(WARN.UnreachableStmtReturn, [statements[k+1]])
            return True, True

    if return_exp and cond_depth == 0:
        ERROR_HANDLER.addError(ERR.NotAllPathsReturn, [func.id.val, func.id])

    return returns, return_exp

'''Given the AST, find dead code statements after return/break/continue and see if all paths return'''
def analyseFunc(ast):
    treemap(ast, lambda node: selectiveApply(AST.FUNDECL, node, lambda f: analyseFuncStmts(f, f.stmts)), replace=False)
    ERROR_HANDLER.checkpoint()

'''
def analyseFunc(symbol_table):
    for (uniq, fun_id), decl_list in symbol_table.functions.items():
        for fundecl in decl_list:
            analyseFuncStmts(fundecl['def'], fundecl['def'].stmts)
'''

'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports
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
            headerfiles = getImportFiles(x, HEADER_EXT, os.path.dirname(args.infile),
                file_mapping_arg=import_mapping,
                lib_dir_path=args.lp,
                lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
            # Get all external symbols
            external_symbol_table = getExternalSymbols(x, headerfiles)
            external_symbol_table = enrichExternalTable(external_symbol_table)
            ERROR_HANDLER.checkpoint()

            symbol_table = buildSymbolTable(x, compiler_target['header'], ext_symbol_table=external_symbol_table)

            print(symbol_table)

            exit()
        else:
            symbol_table = buildSymbolTable(x, compiler_target['header'])
            forbid_illegal_types(symbol_table)
            #analyseFunc(x)
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