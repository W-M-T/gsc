#!/usr/bin/env python3

from lib.analysis.imports import resolveImports
from lib.analysis.error_handler import *
from AST import AST, FunKind, Accessor
from parser import parseTokenStream
from AST_prettyprinter import print_node, subprint_type
from util import Token
import os
from enum import IntEnum

IMPORT_DIR_ENV_VAR_NAME = "SPL_PATH"

# TODO python dict iteration is not deterministically the same: leads to different errros being first every time

class FunUniq(IntEnum):
    FUNC   = 1
    PREFIX = 2
    INFIX  = 3

def FunKindToUniq(kind):
    return {FunKind.FUNC: FunUniq.FUNC,
            FunKind.PREFIX: FunUniq.PREFIX,
            FunKind.INFIXL: FunUniq.INFIX,
            FunKind.INFIXR: FunUniq.INFIX}[kind]

# Keep track if a local is an arg?
# How to handle symbol table merging in case of imports?
# Vars with or without type. Should be able to add type to func params
# Do not forget that even when shadowing arguments or globals, before the definition of this new local, the old one is still in scope (i.e. in earlier vardecls in that function)
class SymbolTable():
    def __init__(self, global_vars = {}, functions = {}, type_syns = {}):
        # mapping of identifier to definition node
        self.global_vars = global_vars

        # (FunUniq, id) as identifier key
        # maps to list of dicts
        # dict has keys "type", "def", "arg_vars", "local_vars"
        # arg_vars is dict of identifiers to dict: {"id":id-token, "type":Type}
        # local_vars is dict of identifiers to vardecl def nodes
        self.functions = functions
        self.type_syns = type_syns

    '''
    def getFunc(self, uniq, fid, normaltype):
        flist = self.functions[(uniq, fid)]
        #x for x in flist if 
        return
    '''


    def repr_funcs(self):
        temp = "\n=Regular:{}\n=Prefix:{}\n=Infix:{}"
        filtered_uniqs = list(map(lambda y: list(filter(lambda x: x[0][0] == y, self.functions.items())), FunUniq))
        filtered_uniqs = list(map(lambda x: "".join(list(map(SymbolTable.repr_func_uniq, x))), filtered_uniqs))
        return temp.format(*filtered_uniqs)

    def repr_func_uniq(func):
        deflist = "\n".join(list(map(lambda x:
                "{} :: {}\n\tArgs:{}\n\tLocals:{}".format(func[0][1], subprint_type(x["type"]), list(x["arg_vars"]), list(x["local_vars"])),
            func[1])))
        return "\n"+deflist

    def repr_short(self):
        return "=== Symbol table:\n== Global vars: {}\n== Functions: {}\n== Type synonyms: {}".format(
            list(self.global_vars.keys()),
            self.repr_funcs(),
            "".join(list(map(lambda x: "\n{} = {}".format(x[0], print_node(x[1])), sorted(self.type_syns.items())))))

    def __repr__(self):
        return self.repr_short()

    '''
    def __repr__(self):
        return "Symbol table:\nGlobal vars: {}\nFunctions: {}\nFunArgs: {}\nLocals: {}\nType synonyms: {}".format(self.global_vars, self.functions, self.funarg_vars, self.local_vars, self.type_syns)
    '''

''' TODO how do we handle imports?? I.e. do we parse the file that we're importing from and then merge the AST's in some way?
I think it would be best if you didn't have to explicitly import dependencies of a function you're importing to have it work, but you also don't want that dependency to end up in the namespace
'''

'''
W.r.t. name resolution:
there's globals, locals and function parameters
'''

''' Maybe move all the builtins to a seperate "StdLib-like" file with both signatures and implementations? '''
''' Fix this data into the correct datatype later using regex on this code '''
BUILTIN_TYPES = [
    "Char",
    "Int",
    "Bool",
    "Void"
]
VOID_TYPE = [
    "Void"
]

BUILTIN_FUNCTIONS = [
    ("print", "T -> Void"),
    ("read", " -> Char"), # TODO Search the spec for what this should do
    ("isEmpty", "[T] -> Bool")
]

# TODO finalize the info in here
BUILTIN_INFIX_OPS = {
    "*": ("T T -> T", 7, "L"),
    "/":  ("T T -> T", 7, "L"),
    "%": ("T T -> T", 7, "L"),
    "+": ("T T -> T", 6, "L"),# Should these actually have types T? It is in the spec but only defined for a couple of types, so maybe it's better to seperate those
    "-": ("T T -> T", 6, "L"),
    ":": ("T [T] -> [T]", 5, "L"),
    "==": ("T T -> Bool", 4, "??"),# How should comparision operators work for lists and tuples? Should they at all?
    "<": ("T T -> Bool", 4, "??"),
    ">": ("T T -> Bool", 4, "??"),
    "<=": ("T T -> Bool", 4, "??"),
    ">=": ("T T -> Bool", 4, "??"),
    "!=": ("T T -> Bool", 4, "??"),
    "&&": ("Bool Bool -> Bool", 3, "R"),
    "||": ("Bool Bool -> Bool", 2, "R")
}

BUILTIN_PREFIX_OPS = [
    ("!", "Bool -> Bool"),
    ("-", "Int -> Int"),
]

ILLEGAL_OP_IDENTIFIERS = [
    "->",
    "::",
    "=",
    "*/"
]


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
            print("Typename {} not defined!".format(inputtype.val))
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
                print("[ERROR] Type synonym {} cannot have Void in its type".format(type_id))
                exit()
            return node

        treemap(type_syn, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require global vars to have a type and not contain Void
    for glob_var_id, glob_var in symbol_table.global_vars.items():

        if glob_var.type is None:
            print('[ERROR] Global var {} needs a type'.format(glob_var.id.val))
            # todo point to line
            exit()
        else:
            def killVoidType(node):
                if type(node.val) is Token and node.val.val == "Void":
                    print("[ERROR] Global variable {} cannot have Void in its type".format(glob_var_id))
                    exit()
                return node
            treemap(glob_var.type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

    # Require function types to not be none, and to not have Void as an input type and no direct Void return Type
    for fun_list in symbol_table.functions.values():
        for fun in fun_list:
            if fun['type'] is None:
                print('[ERROR] Function {} needs a type'.format(fun['def'].id.val))
                exit()
            else:
                def killVoidType(node):
                    if type(node.val) is Token and node.val.val == "Void":
                        print("[ERROR] Input type of {} cannot contain Void".format(fun['def'].id.val))
                        exit()
                    return node
                for from_type in fun['type'].from_types:
                    treemap(from_type, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

                # Forbid non-direct Void return type
                returntype = fun['type'].to_type
                if not (type(returntype) is AST.TYPE and type(returntype.val) is Token and returntype.val.val == "Void"): # Not direct Void type
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == "Void":
                            print("[ERROR] Return type of {} contains nested Void".format(fun['def'].id.val))
                            exit()
                        return node
                    treemap(returntype, lambda x: selectiveApply(AST.TYPE, x, killVoidType))

            # Go over local variable types
            for local_var in fun['local_vars'].values():
                if local_var.type is None:
                    print('[ERROR] Local variable {} of function {} needs a type'.format(local_var.id.val, fun['def'].id.val))
                    exit()
                else:
                    def killVoidType(node):
                        if type(node.val) is Token and node.val.val == "Void":
                            print("[ERROR] Variable {} of function {} has type containing Void".format(local_var.id.val, fun['def'].id.val))
                            exit()
                        return node
                    treemap(local_var, lambda x: selectiveApply(AST.TYPE, x, killVoidType))


''' TODO how should we handle errors / warnings?
E.g. seperate passes for different analyses, with you only receiving errors for the other pass if the pass before it was errorless?
Or should we show the error that is "first" in the file?
How would that work given that some errors in early parts of the program are the result of an analysis result in a later part of the program?

TODO We don't check for redefinition attempts of builtin functions or ops
'''
def buildSymbolTable(ast):
    symbol_table = SymbolTable()

    # TODO Check for duplicates everywhere of course
    print("Imports")
    for el in ast.imports:
        print(el)
    print("Decls")
    for decl in ast.decls:
        val = decl.val
        if type(val) is AST.VARDECL:
            print("Var")
            var_id = val.id.val
            print(var_id)
            if not var_id in symbol_table.global_vars:
                if False: # TODO test if it exists in other module
                    # TODO give warning (doesn't need to be instant, can be collected)
                    # print("[ERROR] This variable was already defined in another module, which is now shadowed")
                    ERROR_HANDLER.addWarning(WARN.ShadowVarOtherModule, [])
                else:
                    symbol_table.global_vars[var_id] = val
            else:
                ERROR_HANDLER.addError(ERR.DuplicateGlobalVarId, [val.id, symbol_table.global_vars[var_id].id])
            #print_node(val)

        elif type(val) is AST.FUNDECL:
            print("Function")
            print_node(val)
            print("params")
            print(val.params)

            # Types are not normalised here yet, because we don't yet have all type syns

            uniq_kind = FunKindToUniq(val.kind)

            if uniq_kind == FunUniq.INFIX:
                pass

            # Test if argument count and type count match
            if val.type is not None:
                from_types = val.type.from_types
                if len(from_types) != len(val.params):
                    ERROR_HANDLER.addError(ERR.ArgCountDoesNotMatchSign, [from_types[0].val.type_id])

            # Test if this function is already defined
            fun_id = val.id.val
            print(fun_id)
            if not (uniq_kind, fun_id) in symbol_table.functions:
                if False: # TODO test if it is already defined in other module
                    pass
                else: # Completely new name
                    symbol_table.functions[(uniq_kind,fun_id)] = []
                    temp_entry = {"type": val.type, "def": val,"arg_vars": {}, "local_vars":{}}

                    funarg_vars = {}
                    local_vars = {}
                    for ix, arg in enumerate(val.params):
                        if not arg.val in funarg_vars:
                            found_type = val.type.from_types[ix] if val.type is not None else None
                            funarg_vars[arg.val] = {"id":arg, "type":found_type}
                        else:
                            ERROR_HANDLER.addError(ERR.DuplicateArgName, [arg])
                    for vardecl in val.vardecls:
                        if vardecl.id.val in funarg_vars:
                            ERROR_HANDLER.addWarning(WARN.ShadowFunArg, [vardecl.id])
                        if not vardecl.id.val in local_vars:
                            local_vars[vardecl.id.val] = vardecl
                        else:
                            ERROR_HANDLER.addError(ERR.DuplicateVarDef, [vardecl.id, local_vars[vardecl.id.val].id])

                    temp_entry["arg_vars"] = funarg_vars
                    temp_entry["local_vars"]  = local_vars

                    #print(temp_entry["arg_vars"]) # TODO we do not as of yet test that all uses of types were defined
                    #exit()
                    symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

            else: # Already defined in the table, check for overloading
                # TODO Dedupe code
                #print("Rewrite this stuff to a single function and call that instead of duplicating code")
                #exit()
                #symbol_table.functions[(uniq_kind,fun_id)] = []
                temp_entry = {"type": val.type, "def": val,"arg_vars": {}, "local_vars":{}}

                funarg_vars = {}
                local_vars = {}
                for ix, arg in enumerate(val.params):
                    if not arg.val in funarg_vars:
                        found_type = val.type.from_types[ix] if val.type is not None else None
                        funarg_vars[arg.val] = {"id":arg, "type":found_type}
                    else:
                        ERROR_HANDLER.addError(ERR.DuplicateArgName, [arg])
                for vardecl in val.vardecls:
                    if vardecl.id.val in funarg_vars:
                        ERROR_HANDLER.addWarning(WARN.ShadowFunArg, [vardecl.id])
                    if not vardecl.id.val in local_vars:
                        local_vars[vardecl.id.val] = vardecl
                    else:
                        ERROR_HANDLER.addError(ERR.DuplicateVarDef, [vardecl.id, local_vars[vardecl.id.val].id])

                temp_entry["arg_vars"] = funarg_vars
                temp_entry["local_vars"]  = local_vars

                #print(temp_entry["arg_vars"]) # TODO we do not as of yet test that all uses of types were defined
                #exit()
                symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

        elif type(val) is AST.TYPESYN:
            #print("Type")
            type_id = val.type_id.val
            def_type = val.def_type

            if type_id in BUILTIN_TYPES:
                ERROR_HANDLER.addError(ERR.ReservedTypeId, [val.type_id])

            if not type_id in symbol_table.type_syns:
                if False: # TODO Test if it exists in another module
                    # TODO give warning (doesn't need to be instant, can be collected)
                    print("[ERROR] This type was already defined in another module, which is now shadowed")
                else:
                    normalized_type = normalizeType(def_type, symbol_table)
                    symbol_table.type_syns[type_id] = normalized_type
            else:
                ERROR_HANDLER.addError(ERR.DuplicateTypeId, [val.type_id])

    print("--------------------------")
    print(symbol_table.repr_short())
    return symbol_table


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(ast, symbol_table):
    glob_vardecl_counter = 0
    glob_typesyn_counter = 0

    for decl in ast.decls:
        val = decl.val
        if type(val) is AST.VARDECL:
            print("Global var decl",glob_vardecl_counter,val)
            val.expr = resolveExprNames(val.expr, symbol_table, glob=True, counter=glob_vardecl_counter)
            glob_vardecl_counter += 1

        elif type(val) is AST.FUNDECL:
            loc_vardecl_counter = 0

            vardecls = val.vardecls
            for vardecl in vardecls:
                print("Local var decl", loc_vardecl_counter, vardecl)
                vardecl.expr = resolveExprNames(vardecl.expr, symbol_table, glob=False, counter=loc_vardecl_counter)
                loc_vardecl_counter +=1

            for stmt in val.stmts:
                print("Stmt")
                # Should do some kind of mapping function here to generalize the recursion over branching and loops

        elif type(val) is AST.TYPESYN:
            print("Let's go BITCHESSSSS!!!!!!!!!!")
            print(resolveTypeName(val.def_type, symbol_table).tree_string())
            pass
    '''
    Funcall naar module, (FunUniq, id) (nog geen type)
    Varref naar module, scope (global of local + naam of arg + naam)
    Type-token naar module, naam of forall type
    '''

# TODO this works differently for typesyns as opposed to other types: typesyns don't allow foralls
def resolveTypeName(typ, symbol_table, counter=-1):
    if type(typ) is AST.TYPE:
        typ.val = resolveTypeName(typ.val, symbol_table, counter=counter)
        return typ
    elif type(typ) is AST.BASICTYPE:
        return typ
    elif type(typ) is AST.TUPLETYPE:
        typ.a = resolveTypeName(typ.a, symbol_table, counter=counter)
        typ.b = resolveTypeName(typ.b, symbol_table, counter=counter)
        return typ
    elif type(typ) is AST.LISTTYPE:
        typ.type = resolveTypeName(typ.type, symbol_table, counter=counter)
        return typ
    elif type(typ) is Token:
        print("GOT A DAMN TOKEN")
        print(typ.val)
        if typ.val in symbol_table.type_syns:
            print(typ, "IS IN THE TABLE!!!!!!!!!!!!!!")
            # Check if it is in scope
            if True: # TODO
                return AST.RES_TYPE(module=None, type_id=typ)
        #Either not in the symbol table or not in scope yet
        if False: # Test if exists in other modules
            pass
        else: # Doesn't exist in other modules either, interpret as forall
            raise Exception("Forall type not implemented")

    else:
        print("GOT SOMETHING ELSE")
        print(typ)


def resolveExprNames(expr, symbol_table, glob=True, counter=-1):
    pass

def buildOperatorTable(symbol_table):
    op_table = BUILTIN_INFIX_OPS

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

    if type(exp[exp_index]) is AST.VARREF or type(exp[exp_index]) is Token: # Literal / identifier
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

''' Parse expressions by performing precedence climbing algorithm. '''
def parseExpression(exp, ops, min_precedence = 1, exp_index = 0):
    result, exp_index = parseAtom(exp, ops, exp_index)

    while True:
        if exp_index < len(exp) and exp[exp_index].val not in ops:
            # TODO: Check that this works
            ERROR_HANDLER.addError(ERR.UndefinedOp, [exp[exp_index]])
            break
        elif exp_index >= len(exp) or ops[exp[exp_index].val][1] < min_precedence:
            break

        if ops[exp[exp_index].val][2] == 'L':
            next_min_prec = ops[exp[exp_index].val][1] + 1
        else:
            next_min_prec = ops[exp[exp_index].val][1]
        op = exp[exp_index]
        exp_index += 1
        rh_expr, exp_index = parseExpression(exp, ops, next_min_prec, exp_index)
        result = AST.PARSEDEXPR(fun=op, arg1=result, arg2=rh_expr)

    return result, exp_index

''' Given the operator table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, op_table):
    decorated_ast = treemap(ast, lambda node: selectiveApply(AST.DEFERREDEXPR, node, lambda y: parseExpression(y.contents, op_table)[0]))

    return decorated_ast

def typecheck(return_stmt):
    pass

# Given an AST node, get first token
def getFirstToken(node):
    pass

'''
Goal of this function is:
- To check for dead code after break/continue statements;
- To check for dead code after return statements;
- To check for break/continue statements outside of loops;
- To check that all paths return if the function should return something
'''
def analyseFuncStmts(statements, loop_depth=0, cond_depth=0):
    returns = False
    return_exp = False
    for k in range(0, len(statements)):
        stmt = statements[k].val
        if type(stmt) is AST.IFELSE:
            return_ctr = 0
            for branch in stmt.condbranches:
                does_return, rexp = analyseFuncStmts(branch.stmts, loop_depth, cond_depth + 1)
                return_exp = return_exp or rexp
                return_ctr += does_return

            if return_ctr == len(stmt.condbranches):
                if k is not len(statements) - 1 and stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    print("[WARNING] The statements after line %d can never be reached because all conditional branches yield a return value.")
                    ERROR_HANDLER.addWarning(WARN.UnreachableStmtBranches, statements[k])
                return True, return_exp
            elif return_ctr > 0 and return_ctr < len(stmt.condbranches):
                return_exp = True

        elif type(stmt) is AST.LOOP:
            returns, return_exp = analyseFuncStmts(stmt.stmts, loop_depth + 1, cond_depth)
            if return_exp:
                returns = False
        elif type(stmt) is AST.BREAK or type(stmt) is AST.CONTINUE:
            if loop_depth == 0:
                ERROR_HANDLER.addError(ERR.BreakOutsideLoop, [stmt.val])
            else:
                if k is not len(statements) - 1:
                    print("[WARNING] The statements after line %d can never be reached because they are preceded by a break or continue.")
                    return False, return_exp
        elif type(stmt) is AST.RETURN:
            typecheck(stmt)
            if k is not len(statements) - 1:
                print("[WARNING] the statements after line %d can never be reached because of a return statement.")
                print(getFirstToken(statements[k+1]))
                ERROR_HANDLER.addWarning(WARN.UnreachableStmtReturn, statements[k+1])
            return True, True

    if return_exp and cond_depth == 0:
        print("[ERROR] Not all paths lead to a (certain) return.")

    return returns, return_exp

'''Given the AST, find dead code statements after return/break/continue and see if all paths return'''
def analyseFunc(ast):
    treemap(ast, lambda node: selectiveApply(AST.FUNDECL, node, lambda f: analyseFuncStmts(f.stmts)), replace=False)

def selectiveApply(typ, node, f):
    if type(node) is typ:
        return f(node)
    return node

def treemap(ast, f, replace=True):
    def unpack(val, f):
        if type(val) == list:
            mapped_list = []
            for el in val:
                mapped_list.append(unpack(el, f))
            return mapped_list
        elif type(val) in AST.nodes:# Require enumlike construct for AST
            return treemap(val, f, replace)
        else:
            return val

    if replace:
        ast = f(ast)
    else:
        f(ast)
    if type(ast) is not Token:
        for attr in ast.items():
            ast[attr[0]] = unpack(attr[1], f)

    return ast

'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports
'''

def analyse(ast, filename):
    #file_mappings = resolveImports(ast, filename)
    #exit()
    symbol_table = buildSymbolTable(ast)
    forbid_illegal_types(symbol_table)
    symbol_table = normalizeAllTypes(symbol_table)

    #ast = resolveNames(ast, symbol_table)
    ast = fixExpression(ast, symbol_table)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Semantic Analysis")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    argparser.add_argument("--lp", metavar="PATH", help="Directory to import libraries from", nargs="?", type=str)
    argparser.add_argument("--im", metavar="LIBNAME:PATH,...", help="Comma-separated library_name:path mapping list, to explicitly specify import paths", type=str)
    args = argparser.parse_args()

    import_mapping = list(map(lambda x: x.split(":"), args.im.split(","))) if args.im is not None else []
    if not (all(map(lambda x: len(x)==2, import_mapping)) and all(map(lambda x: all(map(lambda y: len(y)>0, x)), import_mapping))):
        print("Invalid import mapping")
        exit()
    #print(import_mapping)
    import_mapping = {a:b for (a,b) in import_mapping}
    print("Imports:",import_mapping)

    if not args.infile.endswith(".spl"):
        print("Input file needs to be .spl")
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
String aaa = 2;
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
/*
g (x) {
    return 2;
}//*/
''')
        tokenstream = tokenize(testprog)
        #tokenstream = tokenize(infile)

        x = parseTokenStream(tokenstream, infile)
        #print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        #file_mappings = resolveImports(x, args.infile, import_mapping, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        #print(ERROR_HANDLER)
        symbol_table = buildSymbolTable(x)
        forbid_illegal_types(symbol_table)
        print("NORMALIZING TYPES ==================")
        symbol_table = normalizeAllTypes(symbol_table)
        print("RESOLVING NAMES ====================")
        resolveNames(x, symbol_table)
        exit()
        analyse(x, args.infile)

        print("DONE")