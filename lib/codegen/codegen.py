#!/usr/bin/env python3

from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import *
from lib.datastructure.scope import NONGLOBALSCOPE
from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS
from lib.builtins.functions import BUILTIN_FUNCTIONS

def generate_expr(expr, module_name, mappings):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return ['LDC ' + str(expr.val) if expr.val != 0 else "LDC 00"]
        elif expr.typ is TOKEN.CHAR:
            return ['LDC ' + str(ord(expr.val[1:-1]))]
        elif expr.typ is TOKEN.BOOL:
            return ['LDC -1'] if expr.val else ['LDC 00']
        else:
            raise Exception("Unknown type")
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) == AST.RES_GLOBAL:
            res = []
            module = expr.val.module
            # TODO: This is only debug code
            if expr.val.module is None:
                module = module_name

            res.append('LDC ' + module + '_global_' + expr.val.id.val)
            res.append('LDA 00')

            return res
        else:
            res = []
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                res.append('LDL ' + mappings['vars'][expr.val.id.val])
            else:
                res.append('LDL ' + mappings['args'][expr.val.id.val])

            return res

    elif type(expr) is AST.TYPED_FUNCALL:
        res = []

        for a in expr.args:
            res.extend(generate_expr(a, module_name, mappings))

        module = expr.module if expr.module is not None else module_name

        if expr.module == 'builtins':
            if expr.uniq == FunUniq.FUNC:
                res.append("TRAP 00")
            elif expr.uniq == FunUniq.INFIX:
                res.append(BUILTIN_INFIX_OPS[expr.id.val][3])
            else:
                res.append(BUILTIN_PREFIX_OPS[expr.id.val][2])
        else:
            if expr.uniq == FunUniq.FUNC:
                code_id = expr.id.val
            else:
                code_id = str(mappings['operators'].index((expr.uniq,expr.id.val)))
                print(code_id)

            print("OID")
            print(expr.oid)
            res.append('BSR ' + module + '_{}_'.format(expr.uniq.name.lower()) + code_id + '_' + str(expr.oid))
            if len(expr.args) > 0:
                res.append('AJS -' + str(len(expr.args)))
            res.append('LDR RR')

        return res
    elif type(expr) is AST.TUPLE:
        raise Exception("Not implemented")
    else:
        print(expr)
        print(type(expr))
        raise Exception("Unknown expression type encountered")

def generate_stmts(stmts, label, module_name, mappings, index = 0):

    labels = []
    code = []
    loop_ctr = 0

    for stmt in stmts:
        if type(stmt.val) == AST.RETURN:
            if stmt.val.expr is not None:
                code.extend(generate_expr(stmt.val.expr, module_name, mappings))
                code.append('STR RR')
                code.append('BRA ' + label + '_exit')
            break
        elif type(stmt.val) == AST.ACTSTMT:
            if type(stmt.val.val) == AST.TYPED_FUNCALL:
                code.extend(generate_expr(stmt.val.val, module_name, mappings))
            else:
                if type(stmt.val.val.varref.val) is AST.RES_NONGLOBAL:
                    if stmt.val.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.extend(generate_expr(stmt.val.val.expr, module_name, mappings))
                        code.append('STL ' + mappings['vars'][stmt.val.val.varref.val.id.val])
                    else:
                        code.extend(generate_expr(stmt.val.val.expr, module_name, mappings))
                        code.append('STL ' + mappings['vars'][stmt.val.val.varref.val.id.val])
                else:
                    code.extend(generate_expr(stmt.val.val.expr, module_name, mappings))
                    key = module_name + '_global_' + stmt.val.val.varref.val.id.val
                    code.extend(['LDC ' + key, 'STA 00'])
        elif type(stmt.val) == AST.IFELSE:
            stmts = []
            indices = []
            i = 1
            start_index = index
            for b in stmt.val.condbranches:
                index += 1

                if b.expr is not None:
                    code.extend(generate_expr(b.expr, module_name, mappings))
                    code.append("BRT " + label + "_" + str(index))
                else:
                    code.append("BRA " + label + "_" + str(index))

                branch_stmts, index = generate_stmts(b.stmts, label, module_name, mappings, index)

                if i == len(stmt.val.condbranches) and b.expr is not None:
                    code.append("BRA " + label + "_" + str(index))

                indices.append(index - start_index + loop_ctr)
                stmts.extend(branch_stmts)
                i += 1

            labels.append(code)
            labels.extend(stmts)

            index += 1
            for i in indices:
                labels[i].append("BRA " + label + "_" + str(index))

            code = []
            loop_ctr = index

    labels.append(code)

    print(labels)

    return labels, index

def generate_func(func, symbol_table, module_name, label, mappings):
    print("generating func:",func['def'].id.val)
    code = []

    link_count = '00' #if len(func['arg_vars']) == 0 else str(len(func['arg_vars']))
    code.append('LINK ' + link_count)
    
    arg_index = -2
    for arg in reversed(func['arg_vars']):
        mappings['args'][arg] = str(arg_index)
        arg_index -= 1

    var_index = 1
    for vardecl in func['def'].vardecls:
        mappings['vars'][vardecl.id.val] = str(var_index)
        var_index += 1
        code.extend(generate_expr(vardecl.expr, module_name, mappings))

    stmts_code, _ = generate_stmts(func['def'].stmts, label, module_name, mappings)

    i = 0
    for c in stmts_code:
        if i == 0:
            code.extend(c)
        else:
            if len(c) > 0:
                c[0] = label + '_' + str(i) + ': ' + c[0]
                code.extend(c)
            else:
                # TODO: This is kinda dangerous, just replaces every empty label with a nop
                code.append(label + '_' + str(i) + ': nop')

        i += 1

    code.append(label + '_exit: UNLINK')
    code.append('RET')

    print(code)

    return code

def build_object_file(module_name, global_code, global_labels, function_code):
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
    print(module_name)

    global_code = []
    global_labels = []
    function_code = {}
    mappings = {
        'operators': list(filter(lambda x: x[0] in [FunUniq.INFIX, FunUniq.PREFIX], list(symbol_table.functions.keys()))),
        'args': {},
        'vars': {}
    }

    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        global_labels.append(key)
        global_code.extend(generate_expr(symbol_table.global_vars[g].expr, module_name, mappings))
        global_code.extend(['LDC ' + key, 'STA 00'])

    for f in symbol_table.functions:
        o = 0
        for of in symbol_table.functions[f]:
            key = module_name
            print(of)
            if of['def'].kind is FunKind.PREFIX:
                key += '_prefix_' + str(mappings['operators'].index((FunKindToUniq(of['def'].kind),of['def'].id.val))) + "_"
            elif of['def'].kind  is FunKind.INFIXL or of['def'].kind  is FunKind.INFIXR:
                key += '_infix_' + str(mappings['operators'].index((FunKindToUniq(of['def'].kind),of['def'].id.val))) + "_"
            else:
                key += '_func_' + f[1] + "_"
            key += str(o)
            function_code[key] = generate_func(of, symbol_table, module_name, key, mappings)
            o += 1

    for b in BUILTIN_FUNCTIONS:
        i = 0
        for o in b[1]:
            key = 'builtins_func_' + b[0] + '_' + str(i)
            function_code[key] = o[1]
            i += 1

    gen_code = build_object_file(module_name, global_code, global_labels, function_code)

    return gen_code