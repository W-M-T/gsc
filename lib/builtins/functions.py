#!/usr/bin/env python3

ENTRYPOINT_FUNCNAME = "main"

BUILTIN_FUNCTIONS = {
    "print":
        [
            ("Int -> Void", ["LINK 00", "LDL -2", "TRAP 00", "UNLINK", "RET"]),
            ("Char -> Void", ["LINK 00", "LDL -2", "TRAP 1", "UNLINK", "RET"]),
            ("Bool -> Void", ["LINK 00", "LDL -2", "TRAP 00", "UNLINK", "RET"]),
        ]
     ,
    "read":
        [
            (" -> Int", ["LINK 00", "TRAP 10", "STR RR", "UNLINK", "RET"]),
            (" -> Char", ["LINK 00", "TRAP 11", "STR RR", "UNLINK", "RET"]),
        ]
    ,
    "isEmpty":
        [
            ("[Int] -> Bool", ["nop"]),
            ("[Bool] -> Bool", ["nop"]),
            ("[Char] -> Bool", ["nop"])
        ]
}