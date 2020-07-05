#!/usr/bin/env python3

BUILTIN_INFIX_OPS = {
    "*": (["Int Int -> Int"], 7, "L", "mul"),
    "/": (["Int Int -> Int"], 7, "L", "div"),
    "%": (["Int Int -> Int"], 7, "L", "mod"),
    "+": (["Int Int -> Int", "Char Char -> Char"], 6, "L", "add"),
    "-": (["Int Int -> Int", "Char Char -> Char"], 6, "L", "sub"),
    ":": (["T [T] -> [T]"], 5, "R", None),
    "==": (["T T -> Bool"], 4, "L", "eq"),
    "<": (["T T -> Bool"], 4, "L", "lt"),
    ">": (["T T -> Bool"], 4, "L", "gt"),
    "<=": (["T T -> Bool"], 4, "L", "le"),
    ">=": (["T T -> Bool"], 4, "L", "ge"),
    "!=": (["T T -> Bool"], 4, "L", "ne"),
    "&&": (["Bool Bool -> Bool"], 3, "and"),
    "||": (["Bool Bool -> Bool"], 2, "or")
}

# TODO finalize the info in here

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