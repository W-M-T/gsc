#!/usr/bin/env python3

from lib.datastructure.token import TOKEN
from lib.datastructure.AST import *
from lib.datastructure.scope import NONGLOBALSCOPE
from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS
from lib.builtins.functions import BUILTIN_FUNCTIONS
from enum import IntEnum

class MEMTYPE(IntEnum):
    BASICTYPE   = 1
    POINTER     = 2

def generate_expr(expr, module_name, mappings):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return ['LDC ' + str(expr.val) if expr.val != 0 else "LDC 00"]
        elif expr.typ is TOKEN.CHAR:
            return ['LDC ' + str(ord(expr.val))]
        elif expr.typ is TOKEN.BOOL:
            return ['LDC -1'] if expr.val else ['LDC 00']
        else:
            raise Exception("Unknown type")
    elif type(expr) is AST.PARSEDEXPR:
        return generate_expr(expr.val, module_name, mappings)
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) == AST.RES_GLOBAL:
            res = []
            module = expr.val.module
            # TODO: This is only debug code
            if expr.val.module is None:
                module = module_name

            res.append('LDC ' + module + '_global_' + expr.val.id.val)
            res.append('LDA 00')

            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if field == Accessor.FST or field == Accessor.SND:
                    if field == Accessor.FST:
                        res.append('LDH -1')
                    else:
                        res.append('LDH 00')
                else:
                    raise Exception("Unknown accessor encountered: %s " + field)

            return res
        else:
            res = []
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                res.append('LDL ' + mappings['vars'][expr.val.id.val][0])
            else:
                res.append('LDL ' + mappings['args'][expr.val.id.val][0])

            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if field == Accessor.FST or field == Accessor.SND:
                    if field == Accessor.FST:
                        res.append('LDH -1')
                    else:
                        res.append('LDH 00')
                else:
                    raise Exception("Unknown accessor encountered: %s " + field)

            return res

    elif type(expr) is AST.TYPED_FUNCALL:
        res = []

        for a in expr.args:
            res.extend(generate_expr(a, module_name, mappings))

        module = expr.module if expr.module is not None else module_name

        if expr.module == 'builtins':
            if expr.uniq == FunUniq.FUNC:
                res.extend(BUILTIN_FUNCTIONS[expr.id.val][expr.oid][1])
            elif expr.uniq == FunUniq.INFIX:
                res.append(BUILTIN_INFIX_OPS[expr.id.val][3])
            else:
                res.append(BUILTIN_PREFIX_OPS[expr.id.val][1])
        else:
            if expr.uniq == FunUniq.FUNC:
                code_id = expr.id.val
            else:
                code_id = str(mappings['operators'].index((expr.uniq,expr.id.val)))

            res.append('BSR ' + module + '_{}_'.format(expr.uniq.name.lower()) + code_id + '_' + str(expr.oid))
            if len(expr.args) > 0:
                res.append('AJS -' + str(len(expr.args)))
            res.append('LDR RR')

        return res
    elif type(expr) is AST.TUPLE:
        res = []

        res.extend(generate_expr(expr.a, module_name, mappings))
        res.extend(generate_expr(expr.b, module_name, mappings))
        res.append("STMH 2")

        return res
    else:
        print(expr)
        print(type(expr))
        raise Exception("Unknown expression type encountered")

def generate_ret(stmt, code, module_name, mappings, label):
    if stmt.val.expr is not None:
        code.extend(generate_expr(stmt.val.expr, module_name, mappings))
        code.append('STR RR')
    code.append('BRA ' + label + '_exit')

    return code

def generate_actstmt(stmt, code, module_name, mappings, label):
    if type(stmt.val) == AST.TYPED_FUNCALL:
        code.extend(generate_expr(stmt.val, module_name, mappings))
    else:
        code.extend(generate_expr(stmt.val.expr, module_name, mappings))
        if type(stmt.val.varref.val) is AST.RES_NONGLOBAL:
            if (stmt.val.varref.val.id.val in mappings['vars'] and mappings['vars'][stmt.val.varref.val.id.val][1] == MEMTYPE.BASICTYPE) or (stmt.val.varref.val.id.val in mappings['args'] and mappings['args'][stmt.val.varref.val.id.val][1] == MEMTYPE.BASICTYPE):
                if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                    code.append('STL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                else:
                    code.append('STL ' + mappings['args'][stmt.val.varref.val.id.val][0])
            else:
                if len(stmt.val.varref.val.fields) > 0: # We have accessors
                    fields = list(reversed(stmt.val.varref.val.fields))
                    if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.append('LDL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                    else:
                        code.append('LDL ' + mappings['args'][stmt.val.varref.val.id.val][0])
                    while len(fields) > 1:
                        field = fields.pop()
                        if field == Accessor.FST or field == Accessor.SND:
                            if field == Accessor.FST:
                                code.append('LDH -1')
                            else:
                                code.append('LDH 00')
                        else:
                            raise Exception("Unknown accessor encountered: %s " + field)
                    if fields[0] == Accessor.FST:
                        code.append('STA -1')
                    else:
                        code.append('STA 00')
                else: # No accessors used so we simply overwrite the pointer.
                    if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.append('STL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                    else:
                        code.append('STL ' + mappings['args'][stmt.val.varref.val.id.val][0])

        else:
            key = module_name + '_global_' + stmt.val.varref.val.id.val
            if mappings['globals'][stmt.val.varref.val.id.val] == MEMTYPE.BASICTYPE:
                key = module_name + '_global_' + stmt.val.varref.val.id.val
                code.extend(['LDC ' + key, 'STA 00'])
            else:
                if len(stmt.val.varref.val.fields) > 0: # We have accessors
                    fields = list(reversed(stmt.val.varref.val.fields))
                    code.extend(['LDC ' + key, 'LDA 00'])
                    while len(fields) > 1:
                        field = fields.pop()
                        if field == Accessor.FST or field == Accessor.SND:
                            if field == Accessor.FST:
                                code.append('LDH -1')
                            else:
                                code.append('LDH 00')
                        else:
                            raise Exception("Unknown accessor encountered: %s " + field)
                    if fields[0] == Accessor.FST:
                        code.append('STA -1')
                    else:
                        code.append('STA 00')
                else: # No accessors used so we simply overwrite the pointer.
                    if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.append('STL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                    else:
                        code.append('STL ' + mappings['args'][stmt.val.varref.val.id.val][0])

    return code

def generate_stmts(stmts, label, module_name, mappings, index = 0, loop_label = None):
    code = []

    for stmt in stmts:
        if type(stmt.val) == AST.RETURN:
            code = generate_ret(stmt, code, module_name, mappings, label)
            break
        elif type(stmt.val) == AST.BREAK:
            code.append("BRA " + loop_label + "_exit")
        elif type(stmt.val) == AST.CONTINUE:
            code.append("BRA " + loop_label + "_update")
        elif type(stmt.val) == AST.ACTSTMT:
            code = generate_actstmt(stmt.val, code, module_name, mappings, label)
        elif type(stmt.val) == AST.IFELSE:
            branch_stmts = []
            indices = []
            i = 1

            for b in stmt.val.condbranches:
                index += 1
                indices.append(index)

                # If or elif
                if b.expr is not None:
                    code.extend(generate_expr(b.expr, module_name, mappings))
                    code.append("BRT " + label + "_" + str(index))
                else: # Else
                    code.append("BRA " + label + "_" + str(index))

                branch_stmt, index = generate_stmts(b.stmts, label, module_name, mappings, index, loop_label)

                # Add label to exit in case when there is no else statement
                if i == len(stmt.val.condbranches) and b.expr is not None:
                    code.append("BRA " + label + "_" + str(index + 1))

                branch_stmts.append(branch_stmt)
                i += 1

            index += 1
            i = 0
            for b in branch_stmts:
                # Check if branch does not end in return, if not add exit label
                if not b[-1].endswith("_exit"):
                    b.append("BRA " + label + "_" + str(index))
                b[0] = label + '_' + str(indices[i]) + ': ' + b[0]
                code.extend(b)
                i += 1
            # TODO: This is also generated if all branches return, which is kinda ugly.
            code.append(label + "_" + str(index) + ": nop")

        elif type(stmt.val) == AST.LOOP:
            if stmt.val.init is not None:
                generate_actstmt(stmt.val.init, code, module_name, mappings, label)
            index += 1
            start_index = index

            # Start label
            loop_label = label + "_" + str(index)
            code.append(loop_label + ": nop")

            # Condition
            if stmt.val.cond is not None:
                cond = generate_expr(stmt.val.cond, module_name, mappings)
                code.extend(cond)
                code.append("BRF " + label + "_" + str(start_index) + "_exit")

            # Statements
            branch_stmt, index = generate_stmts(stmt.val.stmts, label, module_name, mappings, index, loop_label)
            code.extend(branch_stmt)

            # Update
            code.append(label + "_" + str(start_index) + "_update: nop")
            if stmt.val.update is not None:
                generate_actstmt(stmt.val.update, code, module_name, mappings, label)

            # Exit
            code.append('BRA ' + label + '_' + str(start_index))
            code.append(label + '_' + str(start_index) + '_exit: nop')

    return code, index

def generate_func(func, symbol_table, module_name, label, mappings):
    print("generating func:",func['def'].id.val)
    code = []

    link_count = '00' #if len(func['arg_vars']) == 0 else str(len(func['arg_vars']))
    code.append('LINK ' + link_count)
    
    arg_index = -2
    for k, arg in reversed(func['arg_vars'].items()):
        memtype = MEMTYPE.POINTER if type(arg['type'].val) == AST.TUPLETYPE or type(arg['type'].val) == AST.LISTTYPE else MEMTYPE.BASICTYPE
        mappings['args'][k] = (str(arg_index), memtype)
        arg_index -= 1

    var_index = 1
    for vardecl in func['def'].vardecls:
        memtype = MEMTYPE.POINTER if type(vardecl.type.val) == AST.TUPLETYPE or type(vardecl.type.val) == AST.LISTTYPE else MEMTYPE.BASICTYPE
        mappings['vars'][vardecl.id.val] = (str(var_index), memtype)
        var_index += 1
        code.extend(generate_expr(vardecl.expr, module_name, mappings))

    stmts_code, _ = generate_stmts(func['def'].stmts, label, module_name, mappings)
    code.extend(stmts_code)

    code.append(label + '_exit: UNLINK')
    code.append('RET')

    print(code)

    return code

def build_object_file(module_name, dependencies, global_code, global_labels, function_code):
    # Depedencies
    object_file = '// DEPENDENCIES:\n'
    for d in dependencies:
        object_file += 'DEPEND ' + d + '\n'

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

def generate_object_file(symbol_table, module_name, dependencies):
    global_code = []
    global_labels = []
    function_code = {}
    mappings = {
        'globals': {},
        'operators': list(filter(lambda x: x[0] in [FunUniq.INFIX, FunUniq.PREFIX], list(symbol_table.functions.keys()))),
        'args': {},
        'vars': {}
    }

    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        global_labels.append(key)
        mappings['globals'][g] = MEMTYPE.POINTER if type(symbol_table.global_vars[g].type.val) == AST.TUPLETYPE or type(symbol_table.global_vars[g].type.val) == AST.LISTTYPE else MEMTYPE.BASICTYPE
        global_code.extend(generate_expr(symbol_table.global_vars[g].expr, module_name, mappings))
        global_code.extend(['LDC ' + key, 'STA 00'])

    for f in symbol_table.functions:
        o = 0
        for of in symbol_table.functions[f]:
            key = module_name
            if of['def'].kind is FunKind.PREFIX:
                key += '_prefix_' + str(mappings['operators'].index((FunKindToUniq(of['def'].kind), of['def'].id.val))) + "_"
            elif of['def'].kind  is FunKind.INFIXL or of['def'].kind  is FunKind.INFIXR:
                key += '_infix_' + str(mappings['operators'].index((FunKindToUniq(of['def'].kind), of['def'].id.val))) + "_"
            else:
                key += '_func_' + f[1] + "_"
            key += str(o)
            function_code[key] = generate_func(of, symbol_table, module_name, key, mappings)
            o += 1

    '''
    for f, b in BUILTIN_FUNCTIONS.items():
        i = 0
        for o in b:
            key = 'builtins_func_' + f + '_' + str(i)
            function_code[key] = o[1]
            i += 1
    '''

    gen_code = build_object_file(module_name, dependencies, global_code, global_labels, function_code)

    return gen_code