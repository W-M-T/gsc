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
    elif type(expr) is AST.RES_VARREF:
        pass
    elif type(expr) is AST.FUNCALL:
        print(expr)
        if expr.kind == FunKind.PREFIX:
            print("test")
    elif type(expr) is AST.TUPLE:
        pass
    else:
        print(type(expr))

def generate_func(func, symbol_table, module_name):
    code = []
    code.append('link')

    code.append('unlink')

    return code

def build_object_file(module_name, global_code, global_labels, function_code):
    object_file = ''

    # Depedencies
    object_file = '// DEPEDENCIES:\n'

    # Init section
    object_file += '// INIT SECTION\n'
    object_file += '\n'.join(global_code)
    object_file += '\n'

    # Entry point
    object_file += '// ENTRYPOINT\n'

    # Global section
    object_file += '// GLOBAL SECTION\n'
    for l in global_labels:
        object_file += l + ': ' + 'nop\n'

    # Function Section
    object_file += '// FUNCTION SECTION\n'
    for l in function_code:
        object_file += l + ': '
        object_file += '\n'.join(function_code[l])
        object_file += '\n'

    # Main
    object_file += '// MAIN\n'
    object_file += 'bra ' + module_name + '_func_main_0\n'
    object_file += 'trap 00'

    return object_file

def generate_object_file(symbol_table, module_name):
    global_code = []
    global_labels = []
    function_code = {}

    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        global_labels.append(key)
        global_code.extend(generate_expr(symbol_table.global_vars[g].expr))
        global_code.extend(['LDC ' + key, 'sta 00'])

    for f in symbol_table.functions:
        o = 0
        for of in symbol_table.functions[f]:
            key = module_name
            if of['def'].kind is FunKind.PREFIX:
                key += '_prefix_'
            elif of['def'].kind  is FunKind.INFIXL or of['def'].kind  is FunKind.INFIXR:
                key += '_infix_'
            else:
                key += '_func_'
            key += f[1] + '_'
            key += str(o)
            function_code[key] = generate_func(o, symbol_table, module_name)
            o += 1

    gen_code = build_object_file(module_name, global_code, global_labels, function_code)
    print(gen_code)
    with open('generated/' + module_name + '.ssmo', 'w+') as fh:
        fh.write(gen_code)