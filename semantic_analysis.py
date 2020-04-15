#!/usr/bin/env python3

from AST import AST, FunKind, Accessor

class SymbolTable():
    pass


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
    ("+", "T T -> T", 6, "L"),# Should these actually have types T? It is in the spec but only defined for a couple of types, so maybe it's better to seperate those
    ("-", "T T -> T", 6, "L"),
    ("*", "T T -> T", 7, "L"),
    ("/", "T T -> T", 7, "L"),
    ("%", "T T -> T", 7, "L"),
    ("==", "T T -> Bool", 4, "??"),# How should comparision operators work for lists and tuples? Should they at all?
    ("<", "T T -> Bool", 4, "??"),
    (">", "T T -> Bool", 4, "??"),
    ("<=", "T T -> Bool", 4, "??"),
    (">=", "T T -> Bool", 4, "??"),
    ("!=", "T T -> Bool", 4, "??"),
    ("&&", "Bool Bool -> Bool", 3, "R"),
    ("||", "Bool Bool -> Bool", 2, "R"),
    (":", "T [T] -> [T]", 5, "L")
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
    symboltable = []

''' Replace all variable occurences that aren't definitions with a kind of reference to the variable definition that it's resolved to '''
def resolveNames(ast):
    pass

''' Given the fixities in the symbol table, properly transform an expression into a tree instead of a list of operators and terms '''
def fixExpression(ast):
    pass

'''
symbol table bevat:
functiedefinities, typenamen en globale variabelen, zowel hier gedefinieerd als in imports


'''


if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Semantic Analysis")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()


    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        tokenlist = list(tokenstream)

        x = SPL.parse_strict(tokenlist, infile)


