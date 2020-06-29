#!/usr/bin/env python3

from lib.imports.imports import export_headers, import_headers, getImportFiles, HEADER_EXT, SOURCE_EXT
from lib.analysis.error_handler import *
from lib.datastructure.AST import AST, FunKind, FunUniq, FunKindToUniq
from lib.datastructure.position import Position
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.symbol_table import SymbolTable
from lib.datastructure.scope import NONGLOBALSCOPE

from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS, ILLEGAL_OP_IDENTIFIERS
from lib.builtins.types import BUILTIN_TYPES, VOID_TYPE
from lib.builtins.functions import BUILTIN_FUNCTIONS

from lib.util.util import treemap, selectiveApply

from lib.parser.parser import parseTokenStream
from lib.debug.AST_prettyprinter import print_node, subprint_type
from enum import IntEnum


IMPORT_DIR_ENV_VAR_NAME = "SPL_PATH"


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
def normalizeType(inputtype, symbol_table):
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
        elif inputtype.val in VOID_TYPE:
            return inputtype
        else:
            print("[ERROR] Typename {} not defined!".format(inputtype.val))
            exit()
    else:
        print("Case not captured:",inputtype)
        exit()

def normalizeAllTypes(symbol_table):
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
Not necessary for types to have been normalised yet, since type syns are checked for void before anything else
'''
def forbid_illegal_types(symbol_table):
    # Require type syns to not contain Void
    for type_id, type_syn in symbol_table.type_syns.items():
        #print(type_syn)
        #print("  a  ")
        def killVoidType(node):
            if type(node.val) is Token and node.val.val == "Void":
                # Type syn has void in type
                ERROR_HANDLER.addError(ERR.TypeSynVoid, [type_id])
            return node

        treemap(type_syn, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require global vars to have a type and not contain Void
    for glob_var_id, glob_var in symbol_table.global_vars.items():

        if glob_var.type is None:
            # Global var has no type (we're doing type checking for now, not inference)
            ERROR_HANDLER.addError(ERR.GlobalVarTypeNone, [glob_var.id.val])
        else:
            def killVoidType(node):
                if type(node.val) is Token and node.val.val == "Void":
                    # Global variable type contains Void
                    ERROR_HANDLER.addError(ERR.GlobalVarVoid, [glob_var_id])
                return node
            treemap(glob_var.type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require function types to not be none, and to not have Void as an input type and no direct Void return Type
    for fun_list in symbol_table.functions.values():
        for fun in fun_list:
            if fun['type'] is None:
                # Function has no type
                ERROR_HANDLER.addError(ERR.FunctionTypeNone, [fun['def'].id.val])
            else:
                def killVoidType(node):
                    if type(node.val) is Token and node.val.val == "Void":
                        # Function input type contains void
                        ERROR_HANDLER.addError(ERR.FunctionInputVoid, [fun['def'].id.val])
                    return node
                for from_type in fun['type'].from_types:
                    treemap(from_type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

                # Forbid non-direct Void return type
                returntype = fun['type'].to_type
                if not (type(returntype) is AST.TYPE and type(returntype.val) is Token and returntype.val.val == "Void"): # Not direct Void type
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == "Void":
                            # Function output contains Void indirectly
                            ERROR_HANDLER.addError(ERR.FunctionOutputNestedVoid, [fun['def'].id.val])
                        return node
                    treemap(returntype, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

            # Go over local variable types
            for local_var in fun['local_vars'].values():
                if local_var.type is None:
                    # Local var has no type
                    ERROR_HANDLER.addError(ERR.LocalVarTypeNone, [local_var.id.val, fun['def'].id.val])
                else:
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == "Void":
                            # Local var has void in type
                            ERROR_HANDLER.addError(ERR.LocalVarVoid, [local_var.id.val, fun['def'].id.val])
                        return node
                    treemap(local_var, lambda x: selectiveApply(AST.TYPE, x, killVoidType))
    ERROR_HANDLER.checkpoint()




'''
Helper function for symbol table building
Return a dict with function info + a dict of local variable definition order
'''
def buildFuncEntry(val):
    temp_entry = {"type": val.type, "def": val,"arg_vars": {}, "local_vars":{}}
    temp_mapping_entry = {"arg_vars": {}, "local_vars": {}}

    funarg_vars = {}
    local_vars = {}
    local_vars_order_mapping = {}
    arg_vars_order_mapping = {}
    for ix, arg in enumerate(val.params):
        if not arg.val in funarg_vars:
            found_type = val.type.from_types[ix] if val.type is not None and ix in range(len(val.type.from_types)) else None
            funarg_vars[arg.val] = {"id":arg, "type":found_type}
            arg_vars_order_mapping[arg.val] = ix
        else:
            # Arg name was already used
            ERROR_HANDLER.addError(ERR.DuplicateArgName, [arg])
    for index_local, vardecl in enumerate(val.vardecls):
        if vardecl.id.val in funarg_vars:
            # The local var id is already an arg id
            ERROR_HANDLER.addWarning(WARN.ShadowFunArg, [vardecl.id])
        if not vardecl.id.val in local_vars:
            local_vars[vardecl.id.val] = vardecl
            local_vars_order_mapping[vardecl.id.val] = index_local
        else:
            # The local var id was already used
            ERROR_HANDLER.addError(ERR.DuplicateVarDef, [vardecl.id, local_vars[vardecl.id.val].id])

    temp_entry["arg_vars"] = funarg_vars
    temp_entry["local_vars"]  = local_vars

    temp_mapping_entry["arg_vars_mapping"] = arg_vars_order_mapping
    temp_mapping_entry["local_vars_mapping"] = local_vars_order_mapping
    return temp_entry, temp_mapping_entry

'''
TODO We don't check for redefinition attempts of builtin functions or ops
'''
def buildSymbolTable(ast, just_for_headerfile=True):
    symbol_table = SymbolTable()

    # Add builtin functions to symbol table:
    #builtin_ops = buildOperatorTable()
    #TODO add this implementation

    # TODO Check for duplicates everywhere of course
    print("Imports")
    for el in ast.imports:
        print(el)
    print("Decls")
    index_global_var = 0
    for decl in ast.decls:
        val = decl.val
        if type(val) is AST.VARDECL:
            print("Var")
            var_id = val.id.val
            print(var_id)
            if not var_id in symbol_table.global_vars: # New global var decl
                if not just_for_headerfile:
                    # TODO test if it exists in other module
                    pass
                    # ERROR_HANDLER.addWarning(WARN.ShadowVarOtherModule, [var_id])
                else:
                    symbol_table.global_vars[var_id] = val
                    symbol_table.order_mapping["global_vars"][var_id] = index_global_var
                    index_global_var += 1
            else:
                # This global var identifier was already used
                ERROR_HANDLER.addError(ERR.DuplicateGlobalVarId, [val.id, symbol_table.global_vars[var_id].id])
            #print(print_node(val))

        elif type(val) is AST.FUNDECL:
            print("Function")
            print(print_node(val))
            print("params")
            print(val.params)

            # Types are not normalised here yet, because we don't yet have all type syns

            uniq_kind = FunKindToUniq(val.kind)

            # Test if argument count and type count match
            if val.type is not None:
                from_types = val.type.from_types
                if len(from_types) != len(val.params):
                    # Arg count doesn't match input type
                    ERROR_HANDLER.addError(ERR.ArgCountDoesNotMatchSign, [val.id])

            # Test if this function is already defined
            fun_id = val.id.val
            print(fun_id)
            if not (uniq_kind, fun_id) in symbol_table.functions:
                if not just_for_headerfile:
                    # TODO test if it is already defined (with the same type) in other module
                    pass
                    # ERROR_HANDLER.addWarning(WARN.ShadowFuncOtherModule, [uniq_kind.name, fun_id, print_node(val.type)])
                else: # Completely new name
                    symbol_table.functions[(uniq_kind,fun_id)] = []
                    symbol_table.order_mapping["local_vars"][(uniq_kind,fun_id)] = []
                    symbol_table.order_mapping["arg_vars"][(uniq_kind,fun_id)] = []

                    temp_entry, temp_order_mapping = buildFuncEntry(val)
                    #print(temp_entry["arg_vars"]) # TODO we do not as of yet test that all uses of types were defined

                    symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)
                    symbol_table.order_mapping["local_vars"][(uniq_kind,fun_id)].append(temp_order_mapping["local_vars_mapping"])
                    symbol_table.order_mapping["arg_vars"][(uniq_kind,fun_id)].append(temp_order_mapping["arg_vars_mapping"])

            else: # Already defined in the table, check for overloading
                temp_entry, temp_order_mapping = buildFuncEntry(val)
                symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)
                symbol_table.order_mapping["local_vars"][(uniq_kind,fun_id)].append(temp_order_mapping["local_vars_mapping"])
                symbol_table.order_mapping["arg_vars"][(uniq_kind,fun_id)].append(temp_order_mapping["arg_vars_mapping"])

        elif type(val) is AST.TYPESYN:
            #print("Type")
            type_id = val.type_id.val
            def_type = val.def_type

            if type_id in BUILTIN_TYPES:
                # Type identifier is reserved
                ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])

            if not type_id in symbol_table.type_syns:
                if not just_for_headerfile:
                    # TODO Test if it exists in another module
                    pass
                    # ERROR_HANDLER.addWarning(WARN.ShadowTypeOtherModule, [type_id])
                else:
                    normalized_type = normalizeType(def_type, symbol_table)
                    symbol_table.type_syns[type_id] = normalized_type
            else:
                # Type identifier already used
                ERROR_HANDLER.addError(ERR.DuplicateTypeId, [val.type_id, symbol_table.type_syns[val.type_id.val]])

    ERROR_HANDLER.checkpoint()

    print("--------------------------")
    print(symbol_table.repr_short())
    return symbol_table


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(symbol_table):
    # Resolve names used in expressions in global variable definitions:
    # Order matters here as to what is in scope

    # Globals
    for glob_var_id, glob_var in symbol_table.global_vars.items():
        in_scope = list(map(lambda x: x[0], filter(lambda x: symbol_table.order_mapping['global_vars'][glob_var_id] > symbol_table.order_mapping['global_vars'][x[0]] ,symbol_table.global_vars.items())))
        glob_var.expr = resolveExprNames(glob_var.expr, symbol_table, glob=True, in_scope_globals=in_scope)

    # Functions
    in_scope_globals = list(symbol_table.global_vars.keys())
    for f in symbol_table.functions: # Functions
        for i in range(0, len(symbol_table.functions[f])): # Overloaded functions
            print(symbol_table.order_mapping['local_vars'][f][i])
            in_scope_locals = {'locals': [], 'args': list(map(lambda x: x[0], symbol_table.functions[f][i]['arg_vars']))}
            for v in symbol_table.functions[f][i]['def'].vardecls:
                in_scope = list(map(lambda x: x[0], filter(
                    lambda x: symbol_table.order_mapping['local_vars'][f][i][v.id.val] > symbol_table.order_mapping['local_vars'][f][i][x[0]],
                    symbol_table.functions[f][i]['local_vars'].items())))

                in_scope_locals['locals'] = in_scope
                resolveExprNames(v.expr, symbol_table, False, in_scope_globals, in_scope_locals)

            in_scope_locals['locals'] = list(symbol_table.functions[f][i]['local_vars'].keys())

            treemap(symbol_table.functions[f][i]['def'], lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: resolveExprNames(y, symbol_table, False, in_scope_globals, in_scope_locals)))

    '''
    Funcall naar module, (FunUniq, id) (nog geen type)
    Varref naar module, scope (global of local + naam of arg + naam)
    Type-token naar module, naam of forall type
    '''

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
                    scope = NONGLOBALSCOPE.GlobalVar
                else:
                    ERROR_HANDLER.addError(ERR.UndefinedVar, [expr.contents[i].id.val, expr.contents[i]])
                    break

                pos = expr.contents[i]._start_pos
                expr.contents[i] = AST.RES_VARREF(val=AST.RES_NONGLOBAL(
                    scope=scope,
                    id=expr.contents[i].id,
                    fields=expr.contents[i].fields
                ))
                expr.contents[i]._start_pos = pos
        elif type(expr.contents[i]) is AST.TUPLE:
            expr.contents[i].a = resolveExprNames(expr.contents[i].a, symbol_table, glob, in_scope_globals, in_scope_locals)
            expr.contents[i].b = resolveExprNames(expr.contents[i].b, symbol_table, glob, in_scope_globals, in_scope_locals)
        elif type(expr.contents[i]) is AST.DEFERREDEXPR:
            expr.contents[i] = resolveExprNames(expr.contents[i], symbol_table, glob, in_scope_globals, in_scope_locals)

    return expr

'''
Given an abstract type (like T) return all of its concrete possibilities as AST nodes.
'''
def abstractToConcreteType(abstract_type, basic_types):
    if abstract_type == 'T':
        return [AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, b)) for b in basic_types]
    elif abstract_type in basic_types:
        return [AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, abstract_type))]
    elif abstract_type == '[T]':
        return [AST.LISTTYPE(type=AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, b))) for b in basic_types]
    else:
        raise Exception("Unknown abstract type encountered in builtin operator table: %s" % abstract_type)

'''
Given the symbol table, produce the operator table including all builtin operators and its overloaded functions.
'''
def buildOperatorTable():
    op_table = {}

    basic_types = ['Int', 'Char', 'Bool']
    for o in BUILTIN_INFIX_OPS:
        op_table[o] = (BUILTIN_INFIX_OPS[o][1], BUILTIN_INFIX_OPS[o][2], [])
        for x in BUILTIN_INFIX_OPS[o][0]:
            first_type, second_type, _, output_type = x.split()
            first_types = abstractToConcreteType(first_type, basic_types)
            second_types = abstractToConcreteType(second_type, basic_types)
            output_types = abstractToConcreteType(output_type, basic_types)

            for ft in first_types:
                for st in second_types:
                        for ot in output_types:
                            if len(first_types) == len(second_types) == len(output_types) == len(basic_types):
                                if AST.equalVals(ft, st) and AST.equalVals(st, ot):
                                    op_table[o][2].append(
                                        AST.FUNTYPE(
                                            from_types=[ft, st],
                                            to_type=ot
                                        )
                                    )
                            else:
                                op_table[o][2].append(
                                    AST.FUNTYPE(
                                        from_types=[ft, st],
                                        to_type=ot
                                    )
                                )

    return op_table

def mergeCustomOps(op_table, symbol_table):
    for x in symbol_table.functions:
        f = symbol_table.functions[x]
        if x[0] is FunUniq.INFIX:
            precedence = 'L' if f[0]['def'].kind == FunKind.INFIXL else 'R'
            # TODO: Do something about this T T -> T thingie
            op_table[x[1]] = ("T T -> T", f[0]['def'].fixity.val, precedence)

    return op_table

''' Parse expression atoms (literals, identifiers, func call, subexpressions, prefixes) '''
def parseAtom(exp, ops, exp_index):

    def recurse(exp, ops):
        recurse_res, _ = parseExpression(exp, ops)
        return recurse_res

    # TODO: Think about lists.
    if type(exp[exp_index]) is AST.RES_VARREF or type(exp[exp_index]) is Token or type(exp[exp_index]) is AST.TUPLE: # Literal / identifier
        res = exp[exp_index]
        return res, exp_index + 1
    elif type(exp[exp_index]) is AST.DEFERREDEXPR: # Sub expression
        return recurse(exp[exp_index].contents, ops), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == 2: # Prefix
        prefix = exp[exp_index]
        sub_expr = recurse(prefix.args, ops)
        return AST.FUNCALL(id=prefix.id, kind=2, args=sub_expr), exp_index + 1
    elif type(exp[exp_index]) is AST.FUNCALL and exp[exp_index].kind == 1: # Function call
        func_args = []
        funcall = exp[exp_index]
        for arg in funcall.args:
            sub_exp = recurse(arg.contents, ops)
            func_args.append(sub_exp)

        return AST.FUNCALL(id=funcall.id, kind=1, args=func_args), exp_index + 1
    else:
        # This should never happen
        print("[COMPILE ERROR] Unexpected token encountered while parsing atomic value in expression.")
        print(type(exp[exp_index]))
        print(exp[exp_index])
        exit(1)

''' Parse expressions by performing precedence climbing algorithm. '''
def parseExpression(exp, ops, min_precedence = 1, exp_index = 0):
    result, exp_index = parseAtom(exp, ops, exp_index)

    while True:
        if exp_index < len(exp) and exp[exp_index].val not in ops:
            # TODO: Check that this works
            ERROR_HANDLER.addError(ERR.UndefinedOp, [exp[exp_index]])
            break
        elif exp_index >= len(exp) or ops[exp[exp_index].val][0] < min_precedence:
            break

        if ops[exp[exp_index].val][1] == 'L':
            next_min_prec = ops[exp[exp_index].val][0] + 1
        else:
            next_min_prec = ops[exp[exp_index].val][0]
        op = exp[exp_index]
        exp_index += 1
        rh_expr, exp_index = parseExpression(exp, ops, next_min_prec, exp_index)
        result = AST.PARSEDEXPR(fun=op, arg1=result, arg2=rh_expr)

    return result, exp_index

''' Given the operator table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, op_table):
    decorated_ast = treemap(ast, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: parseExpression(y.contents, op_table)[0]))

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

'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports
'''

def analyse(ast, filename):
    #file_mappings = resolveImports(ast, filename)
    #exit()
    symbol_table = buildSymbolTable(ast)
    forbid_illegal_types(symbol_table)
    normalizeAllTypes(symbol_table)

    #ast = resolveNames(ast, symbol_table)
    ast = fixExpression(ast, symbol_table)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lib.parser.lexer import tokenize
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
    import_mapping = {a:b for (a,b) in import_mapping}
    print("Imports:",import_mapping)

    if not args.infile.endswith(SOURCE_EXT):
        print("Input file needs to be {}".format(SOURCE_EXT))
        exit()


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
        if False:
            tokenstream = tokenize(testprog)

            x = parseTokenStream(tokenstream, testprog)
            ERROR_HANDLER.setSourceMapping(testprog, None)
        else:
            tokenstream = tokenize(infile)

            x = parseTokenStream(tokenstream, infile)
            ERROR_HANDLER.setSourceMapping(infile, None)

        #ERROR_HANDLER.debug = True
        #ERROR_HANDLER.hidewarn = True
        #print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        #file_mappings = resolveImports(x, args.infile, import_mapping, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        #print(ERROR_HANDLER)

        if not args.H: # We need to actually read the headerfiles of the imports:
            headerfiles = getImportFiles(x, HEADER_EXT, os.path.dirname(args.infile),
                file_mapping_arg=import_mapping,
                lib_dir_path=args.lp,
                lib_dir_env=os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
            print(headerfiles)
            for head in headerfiles:
                data = head['filehandle'].read()
                print(import_headers(data))
            exit()

        symbol_table = buildSymbolTable(x, args.H)
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

        print("DONE")