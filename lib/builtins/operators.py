#!/usr/bin/env python3

BUILTIN_INFIX_OPS = {
    "*": (["Int Int -> Int"], 7, "L", "MUL"),
    "/": (["Int Int -> Int"], 7, "L", "DIV"),
    "%": (["Int Int -> Int"], 7, "L", "MOD"),
    "+": (["Int Int -> Int", "Char Char -> Char"], 6, "L", "ADD"),
    "-": (["Int Int -> Int", "Char Char -> Char"], 6, "L", "SUB"),
    ":": (["T [T] -> [T]"], 5, "R", None),
    "==": (["T T -> Bool"], 4, "L", "EQ"),
    "<": (["T T -> Bool"], 4, "L", "LT"),
    ">": (["T T -> Bool"], 4, "L", "GT"),
    "<=": (["T T -> Bool"], 4, "L", "LE"),
    ">=": (["T T -> Bool"], 4, "L", "GE"),
    "!=": (["T T -> Bool"], 4, "L", "NE"),
    "&&": (["Bool Bool -> Bool"], 3, "L", "AND"),
    "||": (["Bool Bool -> Bool"], 2, "L", "OR")
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