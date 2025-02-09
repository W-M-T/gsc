#!/usr/bin/env python3

import lib.imports.parsec_original as ps
from lib.datastructure.token import *
# There has to be a better way to do this...
import sys
sys.path.insert(0, '../../')

from lib.datastructure.AST import AST

RE_NAME = r"[_A-Z]+"
RE_ATTR = r"[_a-z]+"
RE_SEP = r"\s*,\s*"
RE_BASE = r"\"[A-Z][a-zA-Z0-9_]*\"" # This is duplicated from the lexer (will lead to problems if one is changed without the other)

'''
This file is only used to parse types, since other symbols can be (de)serialised natively
'''

@ps.generate
def BASENAME():
    found_name = yield ps.regex(RE_BASE)
    return Token(None, TOKEN.TYPE_IDENTIFIER, found_name[1:-1])
# None pos may lead to problems with error printing? Check if this is really necessary

@ps.generate
def KEY_VAL():
    arg_name = yield ps.regex(RE_ATTR)
    yield ps.string("=")
    arg_val = yield NODE ^ BASENAME
    return (arg_name, arg_val)

@ps.generate
def NODE():
    found_name = yield ps.regex(RE_NAME)
    node_type = AST.__dict__[found_name]
    yield ps.string("(")
    key_vals = yield ps.sepBy1(KEY_VAL, ps.regex(RE_SEP))
    key_vals = {k:v for (k,v) in key_vals}
    yield ps.string(")")
    return node_type(**key_vals)

def parse_type(x):
    return NODE.parse(x)

if __name__ == "__main__":
    TEST = 'TYPE(val=LISTTYPE(type=TYPE(val=TUPLETYPE(a=TYPE(val=TUPLETYPE(a=TYPE(val=LISTTYPE(type=TYPE(val=LISTTYPE(type=TYPE(val=BASICTYPE(type_id="Char")))))), b=TYPE(val=BASICTYPE(type_id="Int")))), b=TYPE(val=BASICTYPE(type_id="Int"))))))'
    res = NODE.parse(TEST)
    print(res.tree_string())