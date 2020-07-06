#!/usr/bin/env python3

from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import *
from lib.builtins.operators import BUILTIN_INFIX_OPS

def generate_expr(expr):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return ['LDC ' + str(expr.val)]
        elif expr.typ is TOKEN.CHAR:
            return ['LDC ' + str(ord(expr.val[1:-1]))]
        elif expr.typ is TOKEN.BOOL:
            return ['LDC 0xFFFFFFFF'] if expr.val is 'True' else ['LDC 0']
        else:
            pass
    elif type(expr) is AST.TYPEDEXPR:
        if expr.fun.val in BUILTIN_INFIX_OPS and expr.builtin:

            res = generate_expr(expr.arg1)
            res.extend(generate_expr(expr.arg2))
            res.append(BUILTIN_INFIX_OPS[expr.fun.val][3])

            return res
        else:
            raise Exception('Custom operators not yet supported in code generation.')
    elif type(expr) is AST.FUNCALL:
        print(expr)
        if expr.kind == FunKind.PREFIX:
            print("test")
    else:
        print(type(expr))

def build_code(code):
    print('bra main')

    for l in code:
        print(l + ': ', end='')
        for i in code[l]:
            print(i)

def generate_code(symbol_table, module_name):
    code = {}

    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        code[key] = generate_expr(symbol_table.global_vars[g].expr)

    for f in symbol_table.functions:
        pass

    print(code)

    print(build_code(code))