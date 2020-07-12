#!/usr/bin/env python3

ENTRYPOINT_FUNCNAME = "main"

BUILTIN_FUNCTIONS = {
    "print":
        [
            ("Int -> Void", ["TRAP 00"]),
            ("Char -> Void", ["TRAP 1"]),
            ("Bool -> Void", ["TRAP 00"]),
        ],
    "read":
        [
            (" -> Int", ["TRAP 10"]),
            (" -> Char", ["TRAP 11"]),
        ],
    "isEmpty":
        [
            ("[Int] -> Bool", ["nop"]),
            ("[Bool] -> Bool", ["nop"]),
            ("[Char] -> Bool", ["nop"])
        ]
}