#!/usr/bin/env python3

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
    def __init__(self, global_vars = {}, functions = {FunUniq.FUNC: {}, FunUniq.PREFIX: {}, FunUniq.INFIX: {}}, local_vars = {}, type_syns = {}):
        self.global_vars = global_vars
        self.functions = functions # FunUniq -> dicts
        self.local_vars = local_vars
        self.type_syns = type_syns

    def repr_short(self):
        return "Symbol table:\nGlobal vars: {}\nFunctions: {}\nLocals: {}\nType synonyms: {}".format(
            list(self.global_vars.keys()),
            "\nRegular: {}\nPrefix: {}\nInfix {}".format(
                list(self.functions[FunUniq.FUNC].keys()),
                list(self.functions[FunUniq.PREFIX].keys()),
                list(self.functions[FunUniq.INFIX].keys())),
            list(self.local_vars.keys()),
            list(self.type_syns.keys()))

    def __repr__(self):
        return "Symbol table:\nGlobal vars: {}\nFunctions: {}\nLocals: {}\nType synonyms: {}".format(self.global_vars, self.functions, self.local_vars, self.type_syns)

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
                    print("This variable was already defined in another module, which is now shadowed")
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

            uniq_kind = FunKindToUniq(val.kind)

            if uniq_kind == FunUniq.INFIX:
                pass

            # Test if argument count and type count match
            if val.type is not None:
                from_types = val.type.from_types
                if len(from_types) != len(val.params):
                    print("ERROR: Argument count doesn't match type")
                    exit()
            
            # Test if this function is already defined
            fun_id = val.id.val
            print(fun_id)
            if not fun_id in symbol_table.functions[uniq_kind]:
                if False: # TODO test if it is already defined in other module
                    pass
                else: # Completely new name
                    symbol_table.functions[uniq_kind][fun_id] = val
            else: # Already defined in the table, check for overloading
                pass

            print("vars")
            print(val.vardecls)
            for var in val.vardecls:
                # Check if already in locals
                # If yes, give warning and shadow
                # (Over)write in locals
                pass

        elif type(val) is AST.TYPESYN:
            print("Type")
            type_id = val.type_id.val
            def_type = val.def_type

            if type_id in BUILTIN_TYPES:
                print("ERROR: Reserved type identifier: {}".format(type_id))
                exit()

            if not type_id in symbol_table.type_syns:
                if False: # TODO Test if it exists in another module
                    # TODO give warning (doesn't need to be instant, can be collected)
                    print("This type was already defined in another module, which is now shadowed")
                else:
                    symbol_table.type_syns[type_id] = def_type
            else:
                # TODO Give collectable error
                print("ERROR: Type identifier already defined")
                # TODO point to both definitions
                exit()
    print(symbol_table.repr_short())


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(ast, symbol_table):
    glob_vardecl_counter = 0
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
            pass
    '''
    Funcall naar module, (FunUniq, id) (nog geen type)
    Varref naar module, scope (global of local + naam of arg + naam)
    Type-token naar module, naam of forall type
    '''

def resolveExprNames(expr, symbol_table, glob=True, counter=-1):
    pass

def parseAtom(symbol_table, exp, index, min_precedence):
    if type(exp[index]) is AST.VARREF:
        return exp[index]
    elif type(exp[index]) is AST.DEFERREDEXPR:
        print("We are going recursive")
        return parseExpression(symbol_table, exp, index + 1, min_precedence)
    elif type(exp[index] is Token):
        return exp[index]
    else:
        print("I have this thing:")
        print(type(exp[index]))

def parseExpression(symbol_table, exp, index, min_precedence):
    print("running")
    result = parseAtom(symbol_table, exp, index, min_precedence)
    print(result)

    if (index + 1) >= len(exp):
        print("Out of range - returning")
        return result
    else:
        print("%d, %d" % ((index + 1), len(exp)))
        prec, assoc = BUILTIN_INFIX_OPS[exp[index + 1].val][1], BUILTIN_INFIX_OPS[exp[index + 1].val][2]
        print(prec)
        print(assoc)
        while prec > min_precedence:
            if assoc == 'L':
                next_min_prec = prec + 1
            else:
                next_min_prec = prec

            rh_expr = parseExpression(symbol_table, exp, index + 2, next_min_prec)
            result = AST.PARSEDEXPR(fun=exp[index + 1], arg1=result, arg2=rh_expr)

        return result

# Parse expressions by performing precedence climbing algorithm.
''' Given the fixities in the symbol table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, symbol_table):
    print(ast)
    for decl in ast.decls:
        if type(decl) is AST.VARDECL:
            pass
        elif type(decl) is AST.FUNDECL:
            pass

def typecheck(return_stmt):
    pass

def analyseFuncStmts(statements, loop_depth, cond_depth):
    for k in range(0, len(statements)):
        stmt = statements[k].val
        if type(stmt) is AST.IFELSE:
            return_ctr = 0
            for branch in stmt.condbranches:
                return_ctr += analyseFuncStmts(branch.stmts, loop_depth, cond_depth + 1)

            if return_ctr == len(stmt.condbranches):
                if k is not len(statements) - 1 and stmt.condbranches[len(stmt.condbranches) - 1].expr is None:
                    print("Warning: The statements after line %d can never be reached because all conditional branches yield a return value.")
                return True

        elif type(stmt) is AST.LOOP:
            analyseFuncStmts(stmt.stmts, loop_depth + 1, cond_depth)
        elif type(stmt) is AST.BREAK or type(stmt) is AST.CONTINUE:
            if loop_depth == 0:
                print("Error: Using a break or continue statement out of a loop at line %d.")
            else:
                if k is not len(statements) - 1:
                    print("Warning: The statements after line %d can never be reached because they are preceded by a break or continue.")
        elif type(stmt) is AST.RETURN:
            typecheck(stmt)
            if k is not len(statements) - 1:
                print("Warning: the statements after line %d can never be reached because of a return statement.")
            return True

    return False

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

def resolveImports(ast, filename, file_mapping_arg, lib_dir_path, lib_dir_env): # TODO consider what happens when there is a lexing / parse error in one of the imports

    local_dir = os.path.dirname(os.path.realpath(filename))

    filename_asimport = os.path.basename(filename).rstrip(".spl")

    print("Resolving imports..")

    file_graph = [] # Mapping of checked imports to their path and their child imports.

    openlist = [(ast, filename_asimport, os.path.realpath(filename))] # list of imports that have been parsed but haven't had their imports checked yet
    while openlist:
        current = openlist.pop()
        cur_ast, cur_importname, cur_filename = current

        cur_file_vertex = {"filename": cur_filename, "importname": cur_importname, "ast": cur_ast, "imports": set()}
        importlist = cur_ast.imports

        for imp in importlist:
            importname = imp.name.val

            cur_file_vertex["imports"].add(importname)

            if importname in map(lambda x: x["importname"], file_graph):
                # Already found, don't parse
                continue

            # Open file, parse, close and add to list of files to get imports of
            try:
                filehandle, filename = resolveFileName(importname, local_dir, file_mapping_arg=file_mapping_arg, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
                tokenstream = tokenize(filehandle)
                tokenlist = list(tokenstream)

                x = parseTokenStream(tokenstream, filehandle)
                #print(x.tree_string())
                openlist.append((x, importname, filename))
                filehandle.close()
            except FileNotFoundError as e:
                print("Could not locate import: {}".format(importname))
                exit()
        file_graph.append(cur_file_vertex)

    print("Imported the following files:")
    for vertex in file_graph:
        print(vertex["importname"])
    return file_graph

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
    print(import_mapping)
    import_mapping = {a:b for (a,b) in import_mapping}
    print(import_mapping)

    if not args.infile.endswith(".spl"):
        print("Input file needs to be .spl")
        exit()


    with open(args.infile, "r") as infile:
        print(args.infile)
        print(args.lp)
        print(os.path.realpath(args.infile))
        print(os.path.dirname(os.path.realpath(args.infile)))


        from io import StringIO
        testprog = StringIO('''
Int pi = 3;
type Chara = Int
type String = [Char]
infixl 7 % (a, b) :: Int Int -> Int {
    Int result = a;
    Int a = 2;
    while(result > b) {
        result = result - b;
    }
    return result;
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

        #file_mappings = resolveImports(x, args.infile, import_mapping, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)
        symbol_table = buildSymbolTable(x)
        print("RESOLVING NAMES ====================")
        resolveNames(x, symbol_table)
        exit()
        analyse(x, args.infile)

        print("DONE")