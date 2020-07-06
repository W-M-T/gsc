#!/usr/bin/env python3

from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import *
from lib.datastructure.scope import NONGLOBALSCOPE
from lib.builtins.operators import BUILTIN_INFIX_OPS

def generate_expr(expr, var_mapping = {}):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return ['LDC ' + str(expr.val)]
        elif expr.typ is TOKEN.CHAR:
            return ['LDC ' + str(ord(expr.val[1:-1]))]
        elif expr.typ is TOKEN.BOOL:
            return ['LDC 0xFFFFFFFF'] if expr.val == 'True' else ['LDC 00']
        else:
            raise Exception("Unknown type")
    elif type(expr) is AST.TYPEDEXPR:
        if expr.fun.val in BUILTIN_INFIX_OPS and expr.builtin:

            res = generate_expr(expr.arg1, var_mapping)
            res.extend(generate_expr(expr.arg2, var_mapping))
            res.append(BUILTIN_INFIX_OPS[expr.fun.val][3])

            return res
        else:
            raise Exception('Custom operators not yet supported in code generation.')
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) == AST.RES_GLOBAL:
            res = []
            module = expr.val.module
            if expr.val.module is None:
                module = "main"

            res.append('LDC ' + module + '_global_' + expr.val.id.val)
            res.append('LDA 00')

            return res
        else:
            res = []
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                res.append('LDL ' + var_mapping[expr.val.id.val])

            return res

    elif type(expr) is AST.TYPED_FUNCALL:
        if expr.uniq == FunUniq.FUNC:
            print(expr)
            res = []
            res.append('LDR SP')
            res.append('LDC 3')
            res.append('ADD')
            res.append('STR SP')

            for a in expr.args:
                res.extend(generate_expr(a, var_mapping))

            res.append('LDR SP')
            res.append('LDC ' + str(len(expr.args) + 2))
            res.append('SUB')
            res.append('STR SP')

            module = expr.module if expr.module is not None else "test"

            res.append('BSR ' + module + '_func_' + expr.id.val + '_' + str(expr.oid))
            res.append('LDR RR')

            return res
        else:
            raise Exception("Not implemented")
    elif type(expr) is AST.TUPLE:
        pass
    else:
        print(expr)
        print(type(expr))
        raise Exception("Dikke BMW")

def generate_func(func, symbol_table, module_name):
    code = []

    link_count = '00' if len(func['arg_vars']) == 0 else str(len(func['arg_vars']))

    code.append('LINK ' + link_count)

    var_mapping = {}
    var_index = 1
    for vardecl in func['def'].vardecls:
        var_mapping[vardecl.id.val] = '00' if var_index == 0 else str(var_index)
        var_index += 1
        print(vardecl.expr)
        code.extend(generate_expr(vardecl.expr, var_mapping))

    print(var_mapping)

    for stmt in func['def'].stmts:
        if type(stmt.val) == AST.RETURN:
            if stmt.val.expr is not None:
                code.extend(generate_expr(stmt.val.expr, var_mapping))
            code.append('STR RR')
            code.append('UNLINK')
            code.append('RET')

    return code

def build_object_file(module_name, global_code, global_labels, function_code):
    object_file = ''

    # Depedencies
    object_file = '// DEPENDENCIES:\n'

    # Init section
    object_file += '// INIT SECTION\n'
    object_file += '\n'.join(global_code)
    object_file += '\n'

    # Entry point
    object_file += '// ENTRYPOINT\n'
    object_file += 'BRA main\n'

    # Global section
    object_file += '// GLOBAL SECTION\n'
    for l in global_labels:
        object_file += l + ': ' + 'NOP\n'

    # Function Section
    object_file += '// FUNCTION SECTION\n'
    for l in function_code:
        object_file += l + ': '
        object_file += '\n'.join(function_code[l])
        object_file += '\n'

    # Main
    object_file += '// MAIN\n'
    object_file += 'main: BSR ' + module_name + '_func_main_0\n'
    object_file += 'LDR RR\n'
    object_file += 'TRAP 00'

    return object_file

def generate_object_file(symbol_table, module_name):
    global_code = []
    global_labels = []
    function_code = {}

    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        global_labels.append(key)
        global_code.extend(generate_expr(symbol_table.global_vars[g].expr))
        global_code.extend(['LDC ' + key, 'STA 00'])

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
            function_code[key] = generate_func(of, symbol_table, module_name)
            o += 1

    print(function_code)
    gen_code = build_object_file(module_name, global_code, global_labels, function_code)
    print(gen_code)

    with open('generated/' + module_name + '.ssm', 'w+') as fh:
        fh.write(gen_code)