#!/usr/bin/env python3

from lib.builtins.functions import BUILTIN_FUNCTIONS
from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS, ILLEGAL_OP_IDENTIFIERS
from lib.builtins.types import BUILTIN_TYPES, VOID_TYPE, BASIC_TYPES, HIGHER_BUILTIN_TYPES
from lib.datastructure.AST import AST, FunUniq, FunKind
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.position import Position

from lib.datastructure.symbol_table import ExternalTable

from lib.analysis.error_handler import *

from collections import OrderedDict


BUILTINS_NAME = "builtins"

'''
Given an abstract type (like T) return all of its concrete possibilities as AST nodes.
'''
def abstractToConcreteType(abstract_type):
    if abstract_type == 'T':
        return [AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, b)) for b in BASIC_TYPES]
    elif abstract_type in BASIC_TYPES:
        return [AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, abstract_type))]
    elif abstract_type == '[T]':
        return [AST.LISTTYPE(type=AST.TYPE(val=AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, b)))) for b in BASIC_TYPES]
    elif abstract_type in ['[' + x + ']' for x in BASIC_TYPES]:
        return [AST.LISTTYPE(type=AST.TYPE(val=AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, abstract_type[1:-1]))))]
    elif abstract_type in VOID_TYPE:
        return [Token(Position(), TOKEN.TYPE_IDENTIFIER, "Void")]
    else:
        raise Exception("Unknown abstract type encountered in builtin operator table: %s" % abstract_type)

def generateBuiltinFuncs():
    builtin_functions = OrderedDict()
    for f_id, f_list in BUILTIN_FUNCTIONS.items():
        builtin_functions[(FunUniq.FUNC, f_id)] = []

        for typesig_str, _ in f_list:
            vals = typesig_str.split()
            if vals[0] == '->':
                from_types = []
                to_type = abstractToConcreteType((vals[1]))
            else:
                from_types = abstractToConcreteType(vals[0])
                to_type = abstractToConcreteType(vals[2])

            builtin_functions[(FunUniq.FUNC, f_id)].append({
                'type': AST.FUNTYPE(
                    from_types=[] if len(from_types) == 0 else [AST.TYPE(val=from_types[0])],
                    to_type=AST.TYPE(val=to_type[0])
                    ),
                'module': BUILTINS_NAME,
                'orig_id': f_id,
                'fixity': None,
                'kind': FunKind.FUNC
                })

    return builtin_functions

'''
generate the ExternalTable entries for of all the builtin operators.
# TODO refactor this to not use integer indices in lib.builtins.operators and make infixes and prefixes use the same code here and datastructure there
'''
def generateBuiltinOps():
    op_table = OrderedDict()

    for op_id in BUILTIN_INFIX_OPS:
        op_table[(FunUniq.INFIX, op_id)] = []

        for typesig_str in BUILTIN_INFIX_OPS[op_id][0]:
            #print(typesig_str)
            first_type, second_type, _, output_type = typesig_str.split()
            first_types = abstractToConcreteType(first_type)
            second_types = abstractToConcreteType(second_type)
            output_types = abstractToConcreteType(output_type)

            for ft in first_types:
                for st in second_types:
                        for ot in output_types:
                            if len(first_types) == len(second_types) == len(BASIC_TYPES):
                                if AST.equalVals(ft, st) or (type(st) == AST.LISTTYPE and AST.equalVals(ft, st.type.val) and AST.equalVals(ft, ot.type.val)):
                                    op_table[(FunUniq.INFIX, op_id)].append({
                                        'type': AST.FUNTYPE(
                                                from_types=[AST.TYPE(val=ft), AST.TYPE(val=st)],
                                                to_type=AST.TYPE(val=ot)
                                            ),
                                        'module': BUILTINS_NAME,
                                        'orig_id': op_id,
                                        'fixity': BUILTIN_INFIX_OPS[op_id][1],
                                        'kind': BUILTIN_INFIX_OPS[op_id][2]
                                        })
                            else:
                                op_table[(FunUniq.INFIX, op_id)].append({
                                        'type': AST.FUNTYPE(
                                                from_types=[AST.TYPE(val=ft), AST.TYPE(val=st)],
                                                to_type=AST.TYPE(val=ot)
                                            ),
                                        'module': BUILTINS_NAME,
                                        'orig_id': op_id,
                                        'fixity': BUILTIN_INFIX_OPS[op_id][1],
                                        'kind': BUILTIN_INFIX_OPS[op_id][2]
                                        })

    for op_id, (typesig_str, _) in BUILTIN_PREFIX_OPS.items():
        op_table[(FunUniq.PREFIX, op_id)] = []
        in_type, _, out_type = typesig_str.split()
        in_type_node = abstractToConcreteType(in_type)
        out_type_node = abstractToConcreteType(out_type)

        for in_t in in_type_node:
            for out_t in out_type_node:
                op_table[(FunUniq.PREFIX, op_id)].append({
                    'type': AST.FUNTYPE(
                            from_types=[AST.TYPE(val=in_t)],
                            to_type=AST.TYPE(val=out_t)
                        ),
                    'module': BUILTINS_NAME,
                    'orig_id': op_id[0],
                    'fixity': None,
                    'kind': FunKind.PREFIX
                    })

    return op_table

def generateBuiltinTypesyns():
    temp = OrderedDict()
    for name, def_str in HIGHER_BUILTIN_TYPES.items():
        temp[(name, BUILTINS_NAME)] = OrderedDict([
            ('def_type', AST.TYPE(val=abstractToConcreteType(def_str)[0])),
            ('orig_id', name),
            ('decl', None)
        ])

    return temp

# TODO this is broken now
def mergeCustomOps(op_table, symbol_table, module_name):
    for x in symbol_table.functions:
        f = symbol_table.functions[x]
        if x[0] is FunUniq.INFIX:
            if x[1] not in op_table['infix_ops']:
                op_table['infix_ops'][x[1]] = (f[0]['def'].fixity.val, f[0]['def'].kind, [])

            for o in f:
                if op_table['infix_ops'][x[1]][0] == o['def'].fixity.val and op_table['infix_ops'][x[1]][1] == o['def'].kind:
                    ft = AST.FUNTYPE(
                        from_types=[o['type'].from_types[0].val, o['type'].from_types[1].val],
                        to_type=o['type'].to_type.val
                    )
                    cnt = 0
                    for ot in op_table['infix_ops'][x[1]][2]:
                        if AST.equalVals(ft, ot):
                            cnt += 1

                    if cnt == 0:
                        op_table['infix_ops'][x[1]][2].append((ft, module_name))
                    else:
                        ERROR_HANDLER.addError(ERR.DuplicateOpDef, [o['def'].id.val, o['def'].id])
                else:
                    ERROR_HANDLER.addError(ERR.InconsistentOpDecl, [o['def'].id.val, o['def'].id])

        elif x[0] is FunUniq.PREFIX:
            if x[1] not in op_table['prefix_ops']:
                op_table['prefix_ops'][x[1]] = []

            for o in f:
                op_table['prefix_ops'][x[1]].append(
                    (
                        AST.FUNTYPE(
                            from_types=[o['type'].from_types[0].val],
                            to_type=o['type'].to_type.val
                        ),
                        module_name
                    )
                )


def enrichExternalTable(external_table):
    builtin_funcs = generateBuiltinFuncs()
    builtin_ops = generateBuiltinOps()
    builtin_type_syns = generateBuiltinTypesyns()

    temp_functions = OrderedDict(list(builtin_funcs.items()) + list(builtin_ops.items()))

    # Test if type syns of imports clash with builtins
    # Test for function clashes happens after normalisation

    # Merge functions:
    for k,v in temp_functions.items():
        if k not in external_table.functions:
            external_table.functions[k] = []
        external_table.functions[k].extend(v)

    # Merge type syns:
    for k,v in builtin_type_syns.items():
        if k in external_table.type_syns:
            ERROR_HANDLER.addError(ERR.ImportTypeClashBuiltin, [k])
        external_table.type_syns[k] = v
    #ERROR_HANDLER.checkpoint()
    
    return external_table