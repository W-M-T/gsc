#!/usr/bin/env python3

from collections import OrderedDict

ENTRYPOINT_FUNCNAME = "main"

BUILTIN_FUNCTIONS = OrderedDict([
    ("print",
        [
            ("Int -> Void", ["TRAP 00"]),
            ("Char -> Void", ["TRAP 1"]),
            ("Bool -> Void", ["LDC 1", "AND", "TRAP 00"]),
            ("[Char] -> Void", ["BSR print_string"])
        ]),
    ("read",
        [
            (" -> Int", ["TRAP 10"]),
            (" -> Char", ["TRAP 11"]),
        ]),
    ("isEmpty",
        [
            ("[Int] -> Bool", ["LDC 00", "EQ"]),
            ("[Bool] -> Bool", ["LDC 00", "EQ"]),
            ("[Char] -> Bool", ["LDC 00", "EQ"])
        ])
])