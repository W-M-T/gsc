#!/usr/bin/env python3

from lib.datastructure.AST import FunKind

BUILTIN_INFIX_OPS = {
    "*": (["Int Int -> Int"], 7, FunKind.INFIXL, "MUL"),
    "/": (["Int Int -> Int"], 7, FunKind.INFIXL, "DIV"),
    "%": (["Int Int -> Int"], 7, FunKind.INFIXL, "MOD"),
    "+": (["Int Int -> Int", "Char Char -> Char"], 6, FunKind.INFIXL, "ADD"),
    "-": (["Int Int -> Int", "Char Char -> Char"], 6, FunKind.INFIXL, "SUB"),
    ":": (["T [T] -> [T]"], 5, FunKind.INFIXR, None),
    "==": (["T T -> Bool"], 4, FunKind.INFIXL, "EQ"),
    "<": (["T T -> Bool"], 4, FunKind.INFIXL, "LT"),
    ">": (["T T -> Bool"], 4, FunKind.INFIXL, "GT"),
    "<=": (["T T -> Bool"], 4, FunKind.INFIXL, "LE"),
    ">=": (["T T -> Bool"], 4, FunKind.INFIXL, "GE"),
    "!=": (["T T -> Bool"], 4, FunKind.INFIXL, "NE"),
    "&&": (["Bool Bool -> Bool"], 3, FunKind.INFIXL, "AND"),
    "||": (["Bool Bool -> Bool"], 2, FunKind.INFIXL, "OR")
}

# TODO finalize the info in here

BUILTIN_PREFIX_OPS = [
    ("!", "Bool -> Bool", "not"),
    ("-", "Int -> Int", "neg"),
]

ILLEGAL_OP_IDENTIFIERS = [
    "->",
    "::",
    "=",
    "*/"
]