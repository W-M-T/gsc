#!/usr/bin/env python3

from lib.analysis.imports import resolveImports
from lib.analysis.error_handler import ERROR_HANDLER
from AST import AST, FunKind, Accessor
from parser import parseTokenStream
from AST_prettyprinter import print_node
from util import Token
import os
from enum import IntEnum

IMPORT_DIR_ENV_VAR_NAME = "SPL_PATH"


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
        self.global_vars = global_vars

        # (FunUniq, id) as identifier key
        # maps to list of dicts
        # dict has keys "type", "def", "arg_vars", "local_vars"
        self.functions = functions
        self.type_syns = type_syns

    def getFunc(self, uniq, fid, normaltype):
        flist = self.functions[(uniq, fid)]
        #x for x in flist if 
        return 


    def repr_funcs(self):
        temp = "\n=Regular:{}\n=Prefix:{}\n=Infix:{}"
        filtered_uniqs = list(map(lambda y: list(filter(lambda x: x[0][0] == y, self.functions.items())), FunUniq))
        filtered_uniqs = list(map(lambda x: "".join(list(map(SymbolTable.repr_func_uniq, x))), filtered_uniqs))
        return temp.format(*filtered_uniqs)

    def repr_func_uniq(func):
        deflist = "\n".join(list(map(lambda x:
                "{} :: {}\n\tArgs:{}\n\tLocals:{}".format(func[0][1], print_node(x["type"]), list(x["arg_vars"]), list(x["local_vars"])),
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
            normalised_type = symbol_table.type_syns[inputtype.val]
            return normalised_type
        elif inputtype.val in VOID_TYPE:
            return inputtype
        else:
            print("Typename {} not defined!".format(inputtype.val))
            exit()
    else:
        print("Case not captured:",inputtype)
        exit()

def normalizeAllTypes(symbol_table):
    # Normalize function types and find duplicates
    for key, func in symbol_table.functions.items():
        print(key)
        print(func.tree_string())





''' TODO how should we handle errors / warnings?
E.g. seperate passes for different analyses, with you only receiving errors for the other pass if the pass before it was errorless?
Or should we show the error that is "first" in the file?
How would that work given that some errors in early parts of the program are the result of an analysis result in a later part of the program?
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
                    print("[ERROR] This variable was already defined in another module, which is now shadowed")
                else:
                    symbol_table.global_vars[var_id] = val
            else:
                print("[ERROR] Global variable identifier already used.")
                # TODO point to both definitions
                exit()
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
                    print("[ERROR] Argument count doesn't match type")
                    exit()
            
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
                    for arg in val.params:
                        if not arg.val in funarg_vars:
                            funarg_vars[arg.val] = arg
                        else:
                            print("[ERROR] Duplicate argument name",arg.val)
                            exit() # TODO actually include position and information
                    for vardecl in val.vardecls:
                        if vardecl.id.val in funarg_vars:
                            print("[WARNING] Shadowing function argument",vardecl.id.val) # TODO add information
                        if not vardecl.id.val in local_vars:
                            local_vars[vardecl.id.val] = vardecl.id
                        else:
                            print("[ERROR] Duplicate variable definition",vardecl.id.val)
                            exit()

                    temp_entry["arg_vars"] = funarg_vars
                    temp_entry["local_vars"]  = local_vars
                    symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

            else: # Already defined in the table, check for overloading
                # TODO Dedupe code
                temp_entry = {"type": val.type, "def": val,"arg_vars": {}, "local_vars":{}}

                funarg_vars = {}
                local_vars = {}
                for arg in val.params:
                    if not arg.val in funarg_vars:
                        funarg_vars[arg.val] = arg
                    else:
                        print("[ERROR] Duplicate argument name",arg.val)
                        exit() # TODO actually include position and information
                for vardecl in val.vardecls:
                    if vardecl.id.val in funarg_vars:
                        print("[WARNING] Shadowing function argument",vardecl.id.val) # TODO add information
                    if not vardecl.id.val in local_vars:
                        local_vars[vardecl.id.val] = vardecl.id
                    else:
                        print("[ERROR] Duplicate variable definition",vardecl.id.val)
                        exit()

                temp_entry["arg_vars"] = funarg_vars
                temp_entry["local_vars"]  = local_vars
                symbol_table.functions[(uniq_kind,fun_id)].append(temp_entry)

        elif type(val) is AST.TYPESYN:
            #print("Type")
            type_id = val.type_id.val
            def_type = val.def_type

            if type_id in BUILTIN_TYPES:
                print("[ERROR] Reserved type identifier: {}".format(type_id))
                exit()

            if not type_id in symbol_table.type_syns:
                if False: # TODO Test if it exists in another module
                    # TODO give warning (doesn't need to be instant, can be collected)
                    print("[ERROR] This type was already defined in another module, which is now shadowed")
                else:
                    normalized_type = normalizeType(def_type, symbol_table)
                    symbol_table.type_syns[type_id] = normalized_type
            else:
                # TODO Give collectable error
                print("[ERROR] Type identifier already defined")
                # TODO point to both definitions
                exit()
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

# This is really ugly, need to fix this somehow...
index = 0

''' Parse atoms (literals, identifiers or sub expressions) '''
def parseAtom(ops, exp):
    global index
    if type(exp[index]) is AST.VARREF or type(exp[index]) is Token:     # Literal / identifier
        res = exp[index]
        index += 1
        return res
    elif type(exp[index]) is AST.DEFERREDEXPR:     # Sub expression
        saved_index = index
        index = 0
        res = parseExpression(ops, exp[saved_index].contents, 1)
        index = saved_index + 1
        return res
    elif type(exp[index]) is AST.FUNCALL and exp[index].kind == 2:
        print("Prefix operator")
        prefix = exp[index]
        sub_expr = parseExpression(ops, prefix.args, 1)
        return AST.FUNCALL(id=prefix.id, kind=2, args=sub_expr)
    elif type(exp[index]) is AST.FUNCALL and exp[index].kind == 1:
        func_args = []
        funcall = exp[index]
        for arg in funcall.args:
            print(arg)
            sub_exp = parseExpression(ops, arg, 1)
            args.append(sub_exp)

        return AST.FUNCALL(id=funcall.id, kind=1, args=func_args)
    else:
        print("Error: unexpected token encountered while parsing expression.")

''' Parse expressions by performing precedence climbing algorithm. '''
def parseExpression(ops, exp, min_precedence):
    global index
    result = parseAtom(ops, exp)

    while True:
        if (index >= len(exp) or ops[exp[index].val][1] < min_precedence):
            break

        if ops[exp[index].val][2] == 'L':
            next_min_prec = ops[exp[index].val][1] + 1
        else:
            next_min_prec = ops[exp[index].val][1]
        op = exp[index]
        index += 1
        rh_expr = parseExpression(ops, exp, next_min_prec)
        result = AST.PARSEDEXPR(fun=op, arg1=result, arg2=rh_expr)

    return result

def parseExpression2(ops, exp):
    min_precedence = 1
    index = 0

    while index < len(exp):
        if type(exp[index]) is Token and exp[index].val in ops:
            if ops[exp[index].val][1] < min_precedence:
                break

            if ops[exp[index].val][2] == 'L':
                min_precedence = ops[exp[index].val][1] + 1
            else:
                min_precedence = ops[exp[index].val][1]

        if type(exp[index]) is AST.VARREF or type(exp[index]) is Token:
            lhs = exp[index]
        elif type(exp[index]) is AST.DEFERREDEXPR:  # Sub expression
            lhs = parseExpression2(ops, exp[index].contents)
        elif type(exp[index]) is AST.FUNCALL and exp[index].kind == 2:
            sub_expr = parseExpression2(ops, exp[index].args)
            lhs = AST.FUNCALL(id=exp[index].id, kind=2, args=sub_expr)
        else:
            print("Unknown token:")

        print(type(exp[index]))
        print(index)
        index += 1

''' Given the fixities in the symbol table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, symbol_table):
    operators = BUILTIN_INFIX_OPS

    print("Parsing expression:" )
    print(ast)

    for f in symbol_table.functions.items():
        if f[0][0] == 3:
            precedence = 'L' if f[1].kind == FunKind.INFIXL else 'R'
            operators[f[0][1]] = ('Int Int -> Int', f[1].fixity.val, precedence)

    #parseExpression2(operators, ast)

    return parseExpression(operators, ast, 1)

def typecheck(return_stmt):
    pass

def analyseFuncStmts(statements, loop_depth, cond_depth):
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
                    print("Warning: The statements after line %d can never be reached because all conditional branches yield a return value.")
                return True, return_exp
            elif return_ctr > 0 and return_ctr < len(stmt.condbranches):
                return_exp = True

        elif type(stmt) is AST.LOOP:
            returns, return_exp = analyseFuncStmts(stmt.stmts, loop_depth + 1, cond_depth)
            if return_exp:
                returns = False
        elif type(stmt) is AST.BREAK or type(stmt) is AST.CONTINUE:
            if loop_depth == 0:
                print("Error: Using a break or continue statement out of a loop at line %d.")
            else:
                if k is not len(statements) - 1:
                    print("Warning: The statements after line %d can never be reached because they are preceded by a break or continue.")
                    return False, return_exp
        elif type(stmt) is AST.RETURN:
            typecheck(stmt)
            if k is not len(statements) - 1:
                print("Warning: the statements after line %d can never be reached because of a return statement.")
            return True, True

    if return_exp and cond_depth == 0:
        print("Error: Not all paths lead to a (certain) return.")

    return returns, return_exp

'''Given a function AST node, find dead code statements after return/break/continue and see if all paths return'''
def analyseFunc(func_node):
    statements = func_node.stmts

    print("Analysing function %s\n" % func_node.id.val)
    analyseFuncStmts(statements, 0, 0)

'''
def treemap(ast, f):
    def unpack(val,f):
        if type(val) == list:
            for el in val:
                unpack(el)
        if type(val) in AST.nodes:# Require enumlike construct for AST
            treemap(val,f)

    ast = f(ast)
    for attr in ast:
        unpack(attr,f)

symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports
'''

def analyse(ast, filename):
    #file_mappings = resolveImports(ast, filename)
    #exit()
    symbol_table = buildSymbolTable(ast)
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
Int pi = 3;
type Chara = Int
//type Void = Int
type String = [Char]
type OtherInt = Int
type OtherListInt = [OtherInt]
type StringList = [(([String], Int), Chara)]
infixl 7 % (a, b) :: OtherInt Void -> OtherListInt {
    OtherInt result = a;
    Int a = 2;
    while(result > b) {
        result = result - b;
    }
    return result;
}
f (x) :: Char -> Int {
    Int x2 = x;
    Int x = 2;
    return x;
}
f (x) :: Int -> Int {
    Int x2 = x;
    Int x = 2;
    return x;
}
''')
        tokenstream = tokenize(testprog)
        #tokenstream = tokenize(infile)

        x = parseTokenStream(tokenstream, infile)
        print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        file_mappings = resolveImports(x, args.infile, import_mapping, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        #print(ERROR_HANDLER)
        symbol_table = buildSymbolTable(x)
        exit()
        print("NORMALIZING TYPES ==================")
        symbol_table = normalizeAllTypes(symbol_table)
        exit()
        print("RESOLVING NAMES ====================")
        resolveNames(x, symbol_table)
        exit()
        analyse(x, args.infile)

        print("DONE")