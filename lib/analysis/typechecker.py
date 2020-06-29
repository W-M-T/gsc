#!/usr/bin/env python3

from lib.datastructure.position import Position
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import AST, FunKindToUniq
from lib.datastructure.scope import NONGLOBALSCOPE

from lib.debug.AST_prettyprinter import subprint_type

from lib.analysis.error_handler import ERR, ERROR_HANDLER

def tokenToTypeId(token):
    if token.typ == TOKEN.INT:
        return 'Int'
    elif token.typ == TOKEN.CHAR:
        return 'Char'
    elif token.typ == TOKEN.BOOL:
        return 'Bool'
    elif token.typ == TOKEN.STRING:
        return 'String'
    else:
        raise Exception('Unknown token supplied.')

''' Type check the given expression '''
def typecheck(expr, exp_type, symbol_table, op_table, func=None, r=0, noErrors=False):

    if type(expr) is Token:
        val = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, tokenToTypeId(expr)))
        val._start_pos = Position()
        if not AST.equalVals(val, exp_type):
            if r == 0 and not noErrors:
                ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(val), subprint_type(exp_type), expr])
            return False
        return True
    elif type(expr) is AST.PARSEDEXPR:
        incorrect = 0
        alternatives = 0
        for o in op_table[expr.fun.val][2]:
            if AST.equalVals(o.to_type, exp_type):
                alternatives += 1
                type1 = typecheck(expr.arg1, o.from_types[0], symbol_table, op_table, func, r+1, False)
                type2 = typecheck(expr.arg2, o.from_types[1], symbol_table, op_table, func, r+1, False)

                if not type1:
                    incorrect = 1
                elif not type2:
                    incorrect = 2

        if incorrect != 0 and not noErrors:
            # There is no alternative of this operator which has the expected input types.
            ERROR_HANDLER.addError(ERR.UnsupportedOperandType, [expr.fun.val, incorrect, subprint_type(exp_type), expr.fun])
        elif alternatives == 0 and not noErrors:
            # There is no alternative of this operator which has the expected output type
            ERROR_HANDLER.addError(ERR.IncompatibleTypes, [subprint_type(exp_type), expr.fun])
        return True
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) is AST.RES_GLOBAL:
            var_typ = symbol_table.global_vars[expr.val.id.val]
            if not AST.equalVals(var_typ.type.val, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(var_typ.type), subprint_type(exp_type), expr])
                    return True

        elif type(expr.val) is AST.RES_NONGLOBAL:
            typ = None
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                typ = func['local_vars'][expr.val.id.val].type.val
            elif expr.val.scope == NONGLOBALSCOPE.ArgVar:
                typ = func['arg_vars'][expr.val.id.val]['type'].val
            else:
                typ = symbol_table.global_vars[expr.val.id.val].type.val

            if not AST.equalVals(typ, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
                return False
            return True

        return False
    elif type(expr) is AST.FUNCALL:
        identifier = (FunKindToUniq(expr.kind), expr.id.val)
        out_type_matches = []
        i = 0

        if identifier not in symbol_table.functions:
            ERROR_HANDLER.addError(ERR.UndefinedFun, [expr.id.val, expr.id])
            return True

        for o in symbol_table.functions[identifier]:
            if AST.equalVals(o['type'].to_type.val, exp_type) or exp_type is None:
                out_type_matches.append((i, o))
            i += 1

        if len(out_type_matches) == 0:
            if r == 0 and not noErrors and exp_type is not None:
                ERROR_HANDLER.addError(ERR.NoOverloadedFunDef, [expr.id.val, subprint_type(exp_type), expr.id])
            return False

        func_matches = 0
        for o in out_type_matches:
            identifier = (FunKindToUniq(o[1]['def'].kind), o[1]['def'].id.val)
            if len(o[1]['arg_vars']) == len(expr.args):
                order_mapping = symbol_table.order_mapping['arg_vars'][identifier][o[0]]

                input_matches = 0
                for i in range(0, len(expr.args)):
                    arg_var = list(order_mapping.keys())[list(order_mapping.values()).index(i)]
                    res = typecheck(expr.args[i], o[1]['arg_vars'][arg_var]['type'].val, symbol_table, op_table, func, r, noErrors=True)
                    if res:
                        input_matches += 1

                if input_matches == len(expr.args):
                    func_matches += 1

        if func_matches == 0 and not noErrors:
            ERROR_HANDLER.addError(ERR.NoOverloadedFunWithArgs, [expr.id.val, expr.id])
            return False
        elif func_matches > 1 and exp_type is None:
            ERROR_HANDLER.addError(ERR.AmbiguousFunCall , [expr.id.val, expr.id])
            return False
        elif func_matches > 1:
            ERROR_HANDLER.addError(ERR.AmbiguousNestedFunCall, [expr.id.val, expr.id])

        return True

    elif type(expr) is AST.TUPLE:
        if type(exp_type) is not AST.TUPLETYPE:
            ERROR_HANDLER.addError(ERR.UnexpectedTuple, [exp_type.type_id.val, expr])
            return True

        type1 = typecheck(expr.a, exp_type.a.val, symbol_table, op_table, func)
        type2 = typecheck(expr.b, exp_type.b.val, symbol_table, op_table, func)

        return type1 or type2

    else:
        print("Unknown type")
        print(type(expr))

def typecheck_stmts(func, symbol_table, op_table):

    for vardecl in func['def'].vardecls:
        # Typecheck var decls
        typecheck(vardecl.expr, vardecl.type.val, symbol_table, op_table, func)

    stmts = list(reversed(func['def'].stmts))
    ast_boolnode = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Bool"))
    while len(stmts) > 0:
        stmt = stmts.pop()
        if type(stmt.val) == AST.ACTSTMT:
            typ = None
            if hasattr(stmt.val.val, 'varref'):
                if stmt.val.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                    typ = func['local_vars'][stmt.val.val.varref.val.id.val].type.val
                elif stmt.val.val.varref.val.scope == NONGLOBALSCOPE.ArgVar:
                    typ = func['arg_vars'][stmt.val.val.varref.val.id.val].type.val
                else:
                    typ = symbol_table.global_vars[stmt.val.val.varref.val.id.val].type.val

            if type(stmt.val.val) == AST.ASSIGNMENT:
                typecheck(stmt.val.val.expr, typ, symbol_table, op_table, func)
            else: # Fun call
                typecheck(stmt.val.val, typ, symbol_table, op_table, func)

        elif type(stmt.val) == AST.IFELSE:
            for b in stmt.val.condbranches:
                typecheck(b.expr, ast_boolnode, symbol_table, op_table, func)
                stmts.extend(list(reversed(b.stmts)))
        elif type(stmt.val) == AST.LOOP:
            typecheck(stmt.val.cond, ast_boolnode, symbol_table, op_table, func)
            stmts.extend(list(reversed(stmt.val.stmts)))
        elif type(stmt.val) == AST.RETURN:
            # TODO: Add expected type
            typecheck(stmt.val.expr, func['type'].to_type.val, symbol_table, op_table, func)
            pass

    print("Typechecking has finished")

def typecheck_functions(symbol_table, op_table):
    for f in symbol_table.functions:
        i = 0
        for o in symbol_table.functions[f]:
            typecheck_stmts(o, symbol_table, op_table)
            i += 1

def typecheck_globals(symbol_table, op_table):
    for g in symbol_table.global_vars:
        typecheck(symbol_table.global_vars[g].expr, symbol_table.global_vars[g].type.val, symbol_table, op_table)