#!/usr/bin/env python3

from lib.datastructure.AST import FunKind
from collections import OrderedDict

BUILTIN_INFIX_OPS = OrderedDict([
    ("*", (["Int Int -> Int"], 7, FunKind.INFIXL, "MUL")),
    ("/", (["Int Int -> Int"], 7, FunKind.INFIXL, "DIV")),
    ("%", (["Int Int -> Int"], 7, FunKind.INFIXL, "MOD")),
    ("+", (["Int Int -> Int", "Char Char -> Char"], 6, FunKind.INFIXL, "ADD")),
    ("-", (["Int Int -> Int", "Char Char -> Char"], 6, FunKind.INFIXL, "SUB")),
    (":", (["T [T] -> [T]"], 5, FunKind.INFIXR, "STMH 2")),
    ("==", (["T T -> Bool"], 4, FunKind.INFIXL, "EQ")),
    ("<", (["T T -> Bool"], 4, FunKind.INFIXL, "LT")),
    (">", (["T T -> Bool"], 4, FunKind.INFIXL, "GT")),
    ("<=", (["T T -> Bool"], 4, FunKind.INFIXL, "LE")),
    (">=", (["T T -> Bool"], 4, FunKind.INFIXL, "GE")),
    ("!=", (["T T -> Bool"], 4, FunKind.INFIXL, "NE")),
    ("&&", (["Bool Bool -> Bool"], 3, FunKind.INFIXL, "AND")),
    ("||", (["Bool Bool -> Bool"], 2, FunKind.INFIXL, "OR"))
])

BUILTIN_PREFIX_OPS = OrderedDict([
    ("!", ("Bool -> Bool", "NOT")),
    ("-", ("Int -> Int", "NEG")),
])

ILLEGAL_OP_IDENTIFIERS = [
    "->",
    "::",
    "=",
    "*/"
]