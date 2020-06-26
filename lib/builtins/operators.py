#!/usr/bin/env python3

BUILTIN_INFIX_OPS = {
    "*": (["Int Int -> Int"], 7, "L"),
    "/": (["Int Int -> Int"], 7, "L"),
    "%": (["Int Int -> Int"], 7, "L"),
    "+": (["Int Int -> Int", "Char Char -> Char"], 6, "L"),
    "-": (["Int Int -> Int", "Char Char -> Char"], 6, "L"),
    ":": (["T [T] -> [T]"], 5, "L"),
    "==": (["T T -> Bool"], 4, "L"),# How should comparision operators work for lists and tuples? Should they at all?
    "<": (["T T -> Bool"], 4, "L"),
    ">": (["T T -> Bool"], 4, "L"),
    "<=": (["T T -> Bool"], 4, "L"),
    ">=": (["T T -> Bool"], 4, "L"),
    "!=": (["T T -> Bool"], 4, "L"),
    "&&": (["Bool Bool -> Bool"], 3, "R"),
    "||": (["Bool Bool -> Bool"], 2, "R")
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