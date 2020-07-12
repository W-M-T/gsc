#!/usr/bin/env python3

from lib.builtins.functions import BUILTIN_FUNCTIONS
from lib.builtins.operators import BUILTIN_INFIX_OPS, BUILTIN_PREFIX_OPS, ILLEGAL_OP_IDENTIFIERS
from lib.builtins.types import BUILTIN_TYPES, VOID_TYPE, BASIC_TYPES
from lib.datastructure.AST import AST
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.position import Position

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

    builtin_functions = {}
    for f in BUILTIN_FUNCTIONS:
        builtin_functions[f[0]] = []

        for o in f[1]:
            vals = o[0].split()
            if vals[0] == '->':
                from_types = []
                to_type = abstractToConcreteType((vals[1]))
            else:
                from_types = abstractToConcreteType(vals[0])
                to_type = abstractToConcreteType(vals[2])

            builtin_functions[f[0]].append(
                AST.FUNTYPE(
                    from_types=[] if len(from_types) == 0 else [AST.TYPE(val=from_types[0])],
                    to_type=AST.TYPE(val=to_type[0])
                )
            )

    return builtin_functions

'''
Given the symbol table, produce the operator table for of all the builtin operators.
'''
def buildOperatorTable():
    op_table = {'infix_ops': {}, 'prefix_ops': {}}

    for o in BUILTIN_INFIX_OPS:
        op_table['infix_ops'][o] = (BUILTIN_INFIX_OPS[o][1], BUILTIN_INFIX_OPS[o][2], [])
        for x in BUILTIN_INFIX_OPS[o][0]:
            first_type, second_type, _, output_type = x.split()
            first_types = abstractToConcreteType(first_type)
            second_types = abstractToConcreteType(second_type)
            output_types = abstractToConcreteType(output_type)

            for ft in first_types:
                for st in second_types:
                        for ot in output_types:
                            if len(first_types) == len(second_types) == len(BASIC_TYPES):
                                if AST.equalVals(ft, st) or (type(st) == AST.LISTTYPE and AST.equalVals(ft, st.type.val) and AST.equalVals(ft, ot.type.val)):
                                    op_table['infix_ops'][o][2].append((
                                            AST.FUNTYPE(
                                                from_types=[ft, st],
                                                to_type=ot
                                            ),
                                            "builtins"
                                        )
                                    )
                            else:
                                op_table['infix_ops'][o][2].append((
                                        AST.FUNTYPE(
                                            from_types=[ft, st],
                                            to_type=ot
                                        ),
                                        "builtins"
                                    )
                                )

    for o in BUILTIN_PREFIX_OPS:
        op_table['prefix_ops'][o[0]] = []
        in_type, _, out_type = o[1].split()
        in_type_node = abstractToConcreteType(in_type)
        out_type_node = abstractToConcreteType(out_type)

        for in_t in in_type_node:
            for out_t in out_type_node:
                op_table['prefix_ops'][o[0]].append(
                    (
                        AST.FUNTYPE(
                            from_types=[in_t],
                            to_type=out_t
                        ),
                        "builtins"
                    )
                )

    return op_table