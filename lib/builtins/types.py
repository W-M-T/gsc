#!/usr/bin/env python3

from collections import OrderedDict

BASIC_TYPES = [
    "Char",
    "Int",
    "Bool"
]

VOID_TYPE = "Void"

BUILTIN_TYPES = BASIC_TYPES + [VOID_TYPE]

HIGHER_BUILTIN_TYPES = OrderedDict([
    ("String", "[Char]")
])
