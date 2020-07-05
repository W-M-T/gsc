#!/usr/bin/env python3

from lib.datastructure.token import Token, TOKEN
#from lib.datastructure.instruction import Instruction, INSTRUCTION

def generate_expr(expr):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return 'LDC ' + str(expr.val)
        elif expr.typ is TOKEN.CHAR:
            return 'LDC ' + str(ord(expr.val[1:-1]))
        elif expr.typ is TOKEN.BOOL:
            return 'LDC 0xFFFFFFFF' if expr.val is "True" else 'LDC 0'
        else:
            pass
    else:
        pass

def generate_code(symbol_table):
    for g in symbol_table.global_vars:
        print(g)
        print(symbol_table.global_vars[g])
        print(generate_expr(symbol_table.global_vars[g].expr))

    for f in symbol_table.functions:
        pass
