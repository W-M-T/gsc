#!/usr/bin/env python3

from AST import AST, FunKind, Accessor
from parser import SPL
from AST_prettyprinter import print_node
import os

IMPORT_DIR_ENV_VAR_NAME = "SPL_PATH"

# Keep track if a local is an arg?
# How to handle symbol table merging in case of imports?
# Vars with or without type. Should be able to add type to func params
class SymbolTable():
    def __init__(self, global_names = [], local_dict = [], type_syns = {}):
        self.global_names = global_names
        self.local_dict = local_dict
        self.type_syns = type_syns

    def __repr__(self):
        return "Globals: {}\nLocals: {}\nType synonyms: {}".format(self.global_names, self.local_dict, self.type_syns)

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
BUILTIN_INFIX_OPS = [
    ("*", "T T -> T", 7, "L"),
    ("/", "T T -> T", 7, "L"),
    ("%", "T T -> T", 7, "L"),
    ("+", "T T -> T", 6, "L"),# Should these actually have types T? It is in the spec but only defined for a couple of types, so maybe it's better to seperate those
    ("-", "T T -> T", 6, "L"),
    (":", "T [T] -> [T]", 5, "L"),
    ("==", "T T -> Bool", 4, "??"),# How should comparision operators work for lists and tuples? Should they at all?
    ("<", "T T -> Bool", 4, "??"),
    (">", "T T -> Bool", 4, "??"),
    ("<=", "T T -> Bool", 4, "??"),
    (">=", "T T -> Bool", 4, "??"),
    ("!=", "T T -> Bool", 4, "??"),
    ("&&", "Bool Bool -> Bool", 3, "R"),
    ("||", "Bool Bool -> Bool", 2, "R")
]

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

    for el in ast.imports:
        print("Import")
        print(el)
    for decl in ast.decls:
        val = decl.val
        print("Decl")
        if type(val) is AST.VARDECL:
            print("Var")
            print_node(val)

        elif type(val) is AST.FUNDECL:
            print("Function")
            print_node(val)
            print("params")
            print(val.params)

            if val.type is not None:
                from_types = val.type.from_types
                if len(from_types) != len(val.params):
                    # TODO type mismatches param count
                    pass
                for par in val.params:
                    # TODO add typed version of param to local vars
                    pass
            else:
                for par in val.params:
                    # TODO add untyped version of param to local vars
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
            print_node(val)


''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(ast, symbol_table):
    pass

# Parse expressions by performing precedence climbing algorithm.
''' Given the fixities in the symbol table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast, symbol_table):
    pass

'''
def treemap(ast, f):
    def unpack(val,f):
        if type(val) == list:
            for el in val:
                unpack(el)
        if type(val) in AST:# Require enumlike construct for AST
            treemap(val,f)

    ast = f(ast)
    for attr in ast:
        unpack(attr,f)
'''


'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports


'''

def resolveImports(ast, filename, lib_dir_path, lib_dir_env): # TODO consider what happens when there is a parse error in one of the imports

    local_dir = os.path.dirname(os.path.realpath(filename))

    filename_asimport = os.path.basename(filename).rstrip(".spl")

    print("Resolving imports..")

    file_graph = [] # Mapping of fully qualified filenames to fully qualified filenames

    closedlist = []
    openlist = [(ast, filename_asimport, os.path.realpath(filename))] # list of "tree and file that tree is from that need to have their imports checked"
    while openlist:
        current = openlist.pop()
        #print("Current",current)
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
                filehandle, filename = resolveFileName(importname, local_dir, lib_dir_path=lib_dir_path, lib_dir_env=lib_dir_env)
                tokenstream = tokenize(filehandle)
                tokenlist = list(tokenstream)

                x = SPL.parse_strict(tokenlist, filehandle) # Replace this method with the new one that doesn't use SPL
                #print(x.tree_string())
                openlist.append((x, importname, filename))
                filehandle.close()
            except FileNotFoundError as e:
                print("Could not locate import: {}".format(importname))
                exit()
        file_graph.append(cur_file_vertex)
    for vertex in file_graph:
        print(vertex)
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
    file_mappings = resolveImports(ast, filename)
    exit()
    symbol_table = buildSymbolTable(ast)
    ast = resolveNames(ast, symbol_table)
    ast = fixExpressions(ast, symbol_table)


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
infixl 7 % (a, b) :: Int Int -> Int {
    Int result = a;
    Int a = 2;
    while(result > b) {
        result = result - b;
    }
    return result;
}
''')
        #tokenstream = tokenize(testprog)
        tokenstream = tokenize(infile)
        tokenlist = list(tokenstream)

        x = SPL.parse_strict(tokenlist, infile)

        print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        file_mappings = resolveImports(x, args.infile, args.lp, os.environ[IMPORT_DIR_ENV_VAR_NAME] if IMPORT_DIR_ENV_VAR_NAME in os.environ else None)

        exit()
        analyse(x, args.infile)

        print("DONE")