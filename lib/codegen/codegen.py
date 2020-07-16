#!/usr/bin/env python3

from lib.datastructure.token import TOKEN
from lib.datastructure.AST import *
from lib.datastructure.scope import NONGLOBALSCOPE
from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS
from lib.builtins.functions import BUILTIN_FUNCTIONS
from enum import IntEnum
from lib.imports.objectfile_imports import OBJECT_FORMAT, OBJECT_COMMENT_PREFIX
from lib.parser.parser import Accessor_lookup

class MEMTYPE(IntEnum):
    BASICTYPE   = 1
    POINTER     = 2

def generate_expr(expr, module_name, mappings, ext_table):
    if type(expr) is Token:
        if expr.typ is TOKEN.INT:
            return ['LDC ' + str(expr.val) if expr.val != 0 else "LDC 00"]
        elif expr.typ is TOKEN.CHAR:
            return ['LDC ' + str(ord(expr.val))]
        elif expr.typ is TOKEN.BOOL:
            return ['LDC -1'] if expr.val else ['LDC 00']
        elif expr.typ is TOKEN.EMPTY_LIST:
            return ['LDC 00']
        elif expr.typ is TOKEN.STRING:
            raise Exception('Token STRING not yet supported.')
        else:
            raise Exception("Unknown type")
    elif type(expr) is AST.PARSEDEXPR:
        return generate_expr(expr.val, module_name, mappings, ext_table)
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) == AST.RES_GLOBAL:
            res = []
            module = expr.val.module
            if expr.val.module is None:
                module = module_name
                var_name = expr.val.id.val
            else:
                module = expr.val.module
                var_name = ext_table.global_vars[expr.val.id.val]['orig_id']

            res.append('LDC ' + module + '_global_' + var_name)
            res.append('LDA 00')

            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if Accessor_lookup[field.val] == Accessor.FST or Accessor_lookup[field.val] == Accessor.SND:
                    if Accessor_lookup[field.val] == Accessor.FST:
                        res.append('LDH -1')
                    else:
                        res.append('LDH 00')
                else:
                    if Accessor_lookup[field.val] == Accessor.HD:
                        res.append('BSR head')
                        res.append('AJS -1')
                        res.append('LDR RR')
                    else:
                        res.append('BSR tail')
                        res.append('AJS -1')
                        res.append('LDR RR')

            return res
        else:
            res = []


            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                var_offset = mappings['vars'][expr.val.id.val][0]
            else:
                var_offset = mappings['args'][expr.val.id.val][0]

            res.append('LDL ' + var_offset)
            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if Accessor_lookup[field.val] == Accessor.FST or Accessor_lookup[field.val] == Accessor.SND:
                    if Accessor_lookup[field.val] == Accessor.FST:
                        res.append('LDH -1')
                    else:
                        res.append('LDH 00')
                else:
                    if Accessor_lookup[field.val] == Accessor.HD:
                        res.append('BSR head')
                        res.append('AJS -1')
                        res.append('LDR RR')
                    else:
                        res.append('BSR tail')
                        res.append('AJS -1')
                        res.append('LDR RR')

            return res

    elif type(expr) is AST.TYPED_FUNCALL:
        res = []

        for a in expr.args:
            res.extend(generate_expr(a, module_name, mappings, ext_table))

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
                if expr.module is not None:
                    fid = ext_table.functions[(expr.uniq, expr.id.val)][expr.oid]['orig_id']
                else:
                    fid = expr.id.val
            else:
                if expr.module is not None:
                    fid = str(mappings['operators'][module][(expr.uniq, expr.id.val)])
                else:
                    fid = str(mappings['operators'][module][(expr.uniq, expr.id.val)])

            res.append('BSR ' + module + '_{}_'.format(expr.uniq.name.lower()) + fid + '_' + str(expr.oid))
            if len(expr.args) > 0:
                res.append('AJS -' + str(len(expr.args)))
            # TODO: Check this for void functions
            res.append('LDR RR')

        return res
    elif type(expr) is AST.TUPLE:
        res = []

        res.extend(generate_expr(expr.a, module_name, mappings, ext_table))
        res.extend(generate_expr(expr.b, module_name, mappings, ext_table))
        res.append("STMH 2")

        return res
    else:
        print(expr)
        print(type(expr))
        raise Exception("Unknown expression type encountered")

def generate_ret(stmt, code, module_name, mappings, ext_table, label):
    if stmt.val.expr is not None:
        code.extend(generate_expr(stmt.val.expr, module_name, mappings, ext_table))
        code.append('STR RR')
    code.append('BRA ' + label + '_exit')

    return code

def generate_actstmt(stmt, code, module_name, mappings, ext_table, label):
    if type(stmt.val) == AST.TYPED_FUNCALL:
        code.extend(generate_expr(stmt.val, module_name, mappings, ext_table))
    else:
        code.extend(generate_expr(stmt.val.expr, module_name, mappings, ext_table))
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
                        if Accessor_lookup[field.val] == Accessor.FST or Accessor_lookup[field.val] == Accessor.SND:
                            if Accessor_lookup[field.val] == Accessor.FST:
                                code.append('LDH -1')
                            else:
                                code.append('LDH 00')
                        else:
                            if field == Accessor_lookup[field.val] == Accessor.HD:
                                code.append('BSR head')
                                code.append('AJS -1')
                                code.append('LDR RR')
                            else:
                                code.append('BSR tail')
                                code.append('AJS -1')
                                code.append('LDR RR')
                    if Accessor_lookup[fields[0].val] == Accessor.FST or Accessor_lookup[fields[0].val] == Accessor.HD:
                        code.append('STA -1')
                    else:
                        code.append('STA 00')
                else: # No accessors used so we simply overwrite the pointer.
                    if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.append('STL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                    else:
                        code.append('STL ' + mappings['args'][stmt.val.varref.val.id.val][0])

        else:
            module = module_name if stmt.val.varref.val.module is None else stmt.val.varref.val.module
            if module is None:
                module = module_name
                var_name = stmt.val.varref.val.id.val
            else:
                module = stmt.val.varref.val.module
                var_name = ext_table.global_vars[stmt.val.varref.val.id.val]['orig_id']
            key = module + '_global_' + var_name

            if mappings['globals'][module][var_name] == MEMTYPE.BASICTYPE:
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
                            if field == Accessor_lookup[field.val] == Accessor.HD:
                                code.append('BSR head')
                                code.append('AJS -1')
                                code.append('LDR RR')
                            else:
                                code.append('BSR tail')
                                code.append('AJS -1')
                                code.append('LDR RR')
                    if Accessor_lookup[fields[0].val] == Accessor.FST or Accessor_lookup[fields[0].val] == Accessor.HD:
                        code.append('STA -1')
                    else:
                        code.append('STA 00')
                else: # No accessors used so we simply overwrite the pointer.
                    if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        code.append('STL ' + mappings['vars'][stmt.val.varref.val.id.val][0])
                    else:
                        code.append('STL ' + mappings['args'][stmt.val.varref.val.id.val][0])

    return code

def generate_stmts(stmts, label, module_name, mappings, ext_table, index = 0, loop_label = None):
    code = []

    for stmt in stmts:
        if type(stmt.val) == AST.RETURN:
            code = generate_ret(stmt, code, module_name, mappings, ext_table, label)
            break
        elif type(stmt.val) == AST.BREAK:
            code.append("BRA " + loop_label + "_exit")
        elif type(stmt.val) == AST.CONTINUE:
            code.append("BRA " + loop_label + "_update")
        elif type(stmt.val) == AST.ACTSTMT:
            code = generate_actstmt(stmt.val, code, module_name, mappings, ext_table, label)
        elif type(stmt.val) == AST.IFELSE:
            branch_stmts = []
            indices = []
            i = 1

            for b in stmt.val.condbranches:
                index += 1
                indices.append(index)

                # If or elif
                if b.expr is not None:
                    code.extend(generate_expr(b.expr, module_name, mappings, ext_table))
                    code.append("BRT " + label + "_" + str(index))
                else: # Else
                    code.append("BRA " + label + "_" + str(index))

                branch_stmt, index = generate_stmts(b.stmts, label, module_name, mappings, ext_table, index, loop_label)

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
                generate_actstmt(stmt.val.init, code, module_name, mappings, ext_table, label)
            index += 1
            start_index = index

            # Start label
            loop_label = label + "_" + str(index)
            code.append(loop_label + ": nop")

            # Condition
            if stmt.val.cond is not None:
                cond = generate_expr(stmt.val.cond, module_name, mappings, ext_table)
                code.extend(cond)
                code.append("BRF " + label + "_" + str(start_index) + "_exit")

            # Statements
            branch_stmt, index = generate_stmts(stmt.val.stmts, label, module_name, ext_table, mappings, index, loop_label)
            code.extend(branch_stmt)

            # Update
            code.append(label + "_" + str(start_index) + "_update: nop")
            if stmt.val.update is not None:
                generate_actstmt(stmt.val.update, code, module_name, mappings, label)

            # Exit
            code.append('BRA ' + label + '_' + str(start_index))
            code.append(label + '_' + str(start_index) + '_exit: nop')

    return code, index

def generate_func(func, ext_table, module_name, label, mappings):
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
        code.extend(generate_expr(vardecl.expr, module_name, mappings, ext_table))

    stmts_code, _ = generate_stmts(func['def'].stmts, label, module_name, mappings, ext_table)
    code.extend(stmts_code)

    code.append(label + '_exit: UNLINK')
    code.append('RET')

    return code

def build_object_file(dependencies, global_code, global_labels, function_code):
    # Depedencies
    object_file = OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['depend'] + '\n'
    for d in dependencies:
        object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['dependitem'] + d + '\n'

    # Init section
    object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['init'] + '\n'
    object_file += '\n'.join(global_code)
    object_file += '\n'

    # Entry point
    object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['entrypoint'] + '\n'
    object_file += 'BRA main\n'

    # Global section
    object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['globals'] + '\n'
    for l in global_labels:
        object_file += l + ': ' + 'NOP\n'

    # Function Section
    object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['funcs'] + '\n'
    for l in function_code:
        object_file += l + ': '
        object_file += '\n'.join(function_code[l])
        object_file += '\n'

    # Main
    object_file += OBJECT_COMMENT_PREFIX + OBJECT_FORMAT['main'] + '\n'
    object_file += 'main: nop'
    
    return object_file

def generate_object_file(symbol_table, ext_table, headerfiles, module_name, dependencies):
    global_code = []
    global_labels = []
    function_code = {}
    mappings = {
        'globals': {module_name: {}},
        'operators': {module_name: {}},
        'args': {},
        'vars': {}
    }

    # Add local operator mapping
    i = 0
    for k in list(symbol_table.functions.keys()):
        if k[0] in [FunUniq.INFIX, FunUniq.PREFIX]:
            mappings['operators'][module_name][k] = i
        i += 1

    # Add external operator mapping
    for f in ext_table.functions:
        if f[0] in [FunUniq.INFIX, FunUniq.PREFIX]:
            for of in ext_table.functions[f]:
                if of['module'] != 'builtins':
                    if of['module'] not in mappings['operators']:
                        mappings['operators'][of['module']] = {}
                    mappings['operators'][of['module']][(f[0], of['orig_id'])] = list(headerfiles[of['module']]['symbols']['functions']).index((f[0], of['orig_id']))

    # Load global code initialisation and global types
    for g in symbol_table.global_vars:
        key = module_name + '_global_' + g
        global_labels.append(key)
        mappings['globals'][module_name][g] = MEMTYPE.POINTER if type(symbol_table.global_vars[g].type.val) in [AST.TUPLETYPE, AST.LISTTYPE] else MEMTYPE.BASICTYPE
        global_code.extend(generate_expr(symbol_table.global_vars[g].expr, module_name, mappings, ext_table))
        global_code.extend(['LDC ' + key, 'STA 00'])

    # Load external global types
    for g in ext_table.global_vars:
        if ext_table.global_vars[g]['module'] not in mappings['globals']:
            mappings['globals'][ext_table.global_vars[g]['module']] = {}
        mappings['globals'][ext_table.global_vars[g]['module']][ext_table.global_vars[g]['orig_id']] = MEMTYPE.POINTER if type(ext_table.global_vars[g]['type'].val) in [AST.LISTTYPE, AST.TUPLETYPE] else MEMTYPE.BASICTYPE

    # Generate code for all functions
    for f in symbol_table.functions:
        o = 0
        for of in symbol_table.functions[f]:
            key = module_name
            if of['def'].kind is FunKind.PREFIX:
                key += '_prefix_' + str(mappings['operators'][module_name][(FunKindToUniq(of['def'].kind), of['def'].id.val)]) + "_"
            elif of['def'].kind is FunKind.INFIXL or of['def'].kind  is FunKind.INFIXR:
                key += '_infix_' + str(mappings['operators'][module_name][(FunKindToUniq(of['def'].kind), of['def'].id.val)]) + "_"
            else:
                key += '_func_' + f[1] + "_"
            key += str(o)
            function_code[key] = generate_func(of, ext_table, module_name, key, mappings)
            o += 1

    gen_code = build_object_file(dependencies, global_code, global_labels, function_code)

    return gen_code