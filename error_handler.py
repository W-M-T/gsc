#!/usr/bin/env python3

from AST import AST, FunKind, Accessor
from parser import SPL
from AST_prettyprinter import print_node

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

def resolveImports(ast):
    openlist = [ast]
    while openlist:
        current = openlist.pop()
        importlist = current.imports
        print(importlist)

def analyse(ast):
    resolveImports(ast)
    exit()
    symbol_table = buildSymbolTable(ast)
    ast = resolveNames(ast, symbol_table)
    ast = fixExpressions(ast, symbol_table)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Semantic Analysis")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()


    with open(args.infile, "r") as infile:
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
        tokenstream = tokenize(testprog)
        #tokenstream = tokenize(infile)
        tokenlist = list(tokenstream)

        x = SPL.parse_strict(tokenlist, infile)

        #print(x.tree_string())
        #treemap(x, lambda x: x)
        #exit()

        analyse(x)

        print("DONE")