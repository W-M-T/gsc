#!/usr/bin/env python3

from lib.datastructure.position import Position
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import AST, FunKind, FunKindToUniq, FunUniq, Accessor
from lib.datastructure.scope import NONGLOBALSCOPE

from lib.debug.AST_prettyprinter import subprint_type, print_node

from lib.analysis.error_handler import ERR, ERROR_HANDLER

def tokenToNode(token):
    if token.typ == TOKEN.INT:
        node = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Int"))
        node._start_pos = Position()
        return node
    elif token.typ == TOKEN.CHAR:
        node = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Char"))
        node._start_pos = Position()
        return node
    elif token.typ == TOKEN.BOOL:
        node = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Bool"))
        node._start_pos = Position()
        return node
    elif token.typ == TOKEN.STRING:
        node = AST.LISTTYPE(type=AST.TYPE(val=AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Char"))))
        node._start_pos = Position()
        return node
    elif token.typ == TOKEN.EMPTY_LIST:
        node = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "[]"))
        node._start_pos = Position()
        return node
    else:
        raise Exception('Unexpected token type encountered')

# TODO: Void functions
# TODO: Check if Strings ===== [Char]??
# TODO: What about print and get input functions

''' Type check the given expression '''
def typecheck(expr, exp_type, symbol_table, op_table, builtin_funcs = {}, func=None, r=0, noErrors=False):

    if type(expr) is Token:
        if expr.typ == TOKEN.EMPTY_LIST:
            if type(exp_type) == AST.LISTTYPE:
                return True, expr
            else:
                ERROR_HANDLER.addError(ERR.UnexpectedEmptyList, [expr])

        val = tokenToNode(expr)
        if not AST.equalVals(val, exp_type):
            if r == 0 and not noErrors:
                ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(val), subprint_type(exp_type), expr])
            return False, expr

        return True, expr
    elif type(expr) is AST.PARSEDEXPR:
        incorrect = 0
        alternatives = 0
        match = None
        arg1 = None
        arg2 = None

        for o in op_table['infix_ops'][expr.fun.val][2]:
            print(expr.fun.val)
            if AST.equalVals(o[0].to_type, exp_type):
                alternatives += 1
                type1, a1 = typecheck(expr.arg1, o[0].from_types[0], symbol_table, op_table, builtin_funcs, func, r+1, False)
                type2, a2 = typecheck(expr.arg2, o[0].from_types[1], symbol_table, op_table, builtin_funcs, func, r+1, False)

                if not type1:
                    incorrect = 1
                elif not type2:
                    incorrect = 2
                else:
                    match = o
                    arg1 = a1
                    arg2 = a2

        if alternatives == 0 and not noErrors:
            # There is no alternative of this operator which has the expected output type
            ERROR_HANDLER.addError(ERR.IncompatibleTypes, [subprint_type(exp_type), expr.fun])
            return True, expr
        if match is None and not noErrors:
            # There is no alternative of this operator which has the expected input types.
            ERROR_HANDLER.addError(ERR.UnsupportedOperandType, [expr.fun.val, incorrect, subprint_type(exp_type), expr.fun])
            return True, expr
        elif match is not None and func is None and match[1] is False:
            ERROR_HANDLER.addError(ERR.GlobalDefMustBeConstant, [expr.fun])
            return True, expr

        print(expr.fun)

        return True, AST.TYPEDEXPR(fun=expr.fun, arg1=arg1, arg2=arg2, typ=match[0], builtin=match[1])

        # TODO: fix this
        #module = "builtins"
        #if match[1]:
        #    module = "builtins"

        #return True, AST.TYPED_FUNCALL(id=expr.fun, uniq=FunUniq.INFIX, args=[arg1, arg2], module=module)
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) is AST.RES_GLOBAL:
            typ = symbol_table.global_vars[expr.val.id.val].type.val

            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if field == Accessor.FST or field == Accessor.SND:
                    if type(typ) is AST.TUPLETYPE:
                        if field == Accessor.FST:
                            typ = typ.a.val
                        else:
                            typ = typ.b.val
                    else:
                        ERROR_HANDLER.addError(ERR.IllegalTupleAccessorUsage, [expr])
                elif field == Accessor.HD or field == Accessor.TL:
                    if type(typ) is AST.LISTTYPE:
                        typ = typ.type.val
                    else:
                        ERROR_HANDLER.addError(ERR.IllegalListAccessorUsage, [expr])
                else:
                    raise Exception("Unknown accessor encountered: %s " % str(field))

            if not AST.equalVals(typ, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
                return False, expr

        elif type(expr.val) is AST.RES_NONGLOBAL:
            typ = None
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                typ = func['local_vars'][expr.val.id.val].type.val
            elif expr.val.scope == NONGLOBALSCOPE.ArgVar:
                typ = func['arg_vars'][expr.val.id.val]['type'].val
            else:
                raise Exception("I want to hear this...")

            fields = list(reversed(expr.val.fields))
            while len(fields) > 0:
                field = fields.pop()
                if field == Accessor.FST or field == Accessor.SND:
                    if type(typ) is AST.TUPLETYPE:
                        if field == Accessor.FST:
                            typ = typ.a.val
                        else:
                            typ = typ.b.val
                    else:
                        ERROR_HANDLER.addError(ERR.IllegalTupleAccessorUsage, [expr])
                elif field == Accessor.HD or field == Accessor.TL:
                    if type(typ) is AST.LISTTYPE:
                        typ = typ.type.val
                    else:
                        ERROR_HANDLER.addError(ERR.IllegalListAccessorUsage, [expr])
                else:
                    raise Exception("Unknown accessor encountered: %s " % str(field))

            if not AST.equalVals(typ, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
                return False, expr

        return True, expr
    elif type(expr) is AST.FUNCALL:
        if expr.kind == FunKind.PREFIX:
            out_type_matches = []
            for op in op_table['prefix_ops'][expr.id.val]:
                if AST.equalVals(op[0].to_type, exp_type):
                    out_type_matches.append(op)

            if len(out_type_matches) == 0:
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.NoPrefixDefWithType, [expr.id.val, subprint_type(exp_type), expr.id])
                return False, expr

            matches = 0
            match = None
            # TODO: Set return args
            for m in out_type_matches:
                res, _ = typecheck(expr.args, m[0].from_types[0], symbol_table, op_table, builtin_funcs, func, r, noErrors=True)

                if res:
                    matches += 1
                    match = m

            if matches == 0:
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.NoPrefixWithInputType, [expr.id.val, expr.id])
                return False, expr
            else:
                if match is not None and func is None and match[1] is False:
                    ERROR_HANDLER.addError(ERR.GlobalDefMustBeConstant, [expr.id])

            return True, expr

        else:
            if func is None:
                ERROR_HANDLER.addError(ERR.GlobalDefMustBeConstant, [expr.id])
                return True, expr

            identifier = (FunKindToUniq(expr.kind), expr.id.val)
            if identifier not in symbol_table.functions and expr.id.val not in builtin_funcs:
                ERROR_HANDLER.addError(ERR.UndefinedFun, [expr.id.val, expr.id])
                return True, expr

            # Builtin functions

            if expr.id.val in builtin_funcs:
                out_type_matches = []
                i = 0
                for o in builtin_funcs[expr.id.val]:
                    if AST.equalVals(o.to_type.val, exp_type) or exp_type is None:
                        out_type_matches.append((i, o))
                    i += 1

                func_matches = 0
                match = None
                match_args = []
                for o in out_type_matches:
                    args = []

                    # TODO: You can make better errors for this
                    if len(o[1].from_types) == len(expr.args):
                        input_matches = 0

                        for i in range(len(o[1].from_types)):
                            typ, arg_res = typecheck(expr.args[i], o[1].from_types[i].val, symbol_table, op_table,
                                                     builtin_funcs, func, r, noErrors=True)
                            args.append(arg_res)
                            if typ:
                                input_matches += 1

                        if input_matches == len(expr.args):
                            func_matches += 1
                            match = o
                            match_args = args

                if match is not None:
                    return True, AST.TYPED_FUNCALL(id=expr.id, uniq=FunKindToUniq(expr.kind), args=match_args, oid=match[0],
                                                   module="builtins")

            # Other functions
            out_type_matches = []
            i = 0
            for o in symbol_table.functions[identifier]:
                if AST.equalVals(o['type'].to_type.val, exp_type) or exp_type is None:
                    out_type_matches.append((i, o))
                i += 1

            if len(out_type_matches) == 0:
                if r == 0 and not noErrors and exp_type is not None:
                    ERROR_HANDLER.addError(ERR.NoOverloadedFunDef, [expr.id.val, subprint_type(exp_type), expr.id])
                return False, expr

            func_matches = 0
            match = None
            match_args = []
            for o in out_type_matches:
                identifier = (FunKindToUniq(o[1]['def'].kind), o[1]['def'].id.val)
                args = []

                # TODO: You can make better errors for this
                if len(o[1]['arg_vars']) == len(expr.args):
                    input_matches = 0

                    i = 0
                    for a in o[1]['arg_vars']:
                        typ, arg_res = typecheck(expr.args[i], o[1]['arg_vars'][a]['type'].val, symbol_table, op_table, builtin_funcs, func, r, noErrors=True)
                        args.append(arg_res)
                        if typ:
                            input_matches += 1
                        i += 1

                    if input_matches == len(expr.args):
                        func_matches += 1
                        match = o
                        match_args = args

            if func_matches == 0:
                if not noErrors:
                    ERROR_HANDLER.addError(ERR.NoOverloadedFunWithArgs, [expr.id.val, expr.id])
                return False, expr
            elif func_matches > 1 and exp_type is None:
                ERROR_HANDLER.addError(ERR.AmbiguousFunCall , [expr.id.val, expr.id])
                return False
            elif func_matches > 1:
                ERROR_HANDLER.addError(ERR.AmbiguousNestedFunCall, [expr.id.val, expr.id])

            return True, AST.TYPED_FUNCALL(id=expr.id, uniq=FunKindToUniq(expr.kind), args=match_args, oid=match[0], module=None)

    elif type(expr) is AST.TUPLE:
        if type(exp_type) is not AST.TUPLETYPE:
            ERROR_HANDLER.addError(ERR.UnexpectedTuple, [exp_type.type_id.val, expr])
            return True, expr

        type1 = typecheck(expr.a, exp_type.a.val, symbol_table, op_table, builtin_funcs, func)
        type2 = typecheck(expr.b, exp_type.b.val, symbol_table, op_table, builtin_funcs, func)

        return type1 or type2, expr

    else:
        raise Exception('Unknown type of expression encountered in typechecking')

def typecheck_stmts(func, symbol_table, op_table, builtin_funcs):
    for vardecl in func['def'].vardecls:
        _, vardecl.expr = typecheck(vardecl.expr, vardecl.type.val, symbol_table, op_table, builtin_funcs, func)

    stmts = list(reversed(func['def'].stmts))
    ast_boolnode = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Bool"))
    while len(stmts) > 0:
        stmt = stmts.pop()
        if type(stmt.val) == AST.ACTSTMT:
            typ = None
            if hasattr(stmt.val.val, 'varref'):
                if type(stmt.val.val.varref.val) == AST.RES_NONGLOBAL:
                    if stmt.val.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                        typ = func['local_vars'][stmt.val.val.varref.val.id.val].type.val
                    else:
                        typ = func['arg_vars'][stmt.val.val.varref.val.id.val]['type'].val
                else:
                    typ = symbol_table.global_vars[stmt.val.val.varref.val.id.val].type.val

            if type(stmt.val.val) == AST.ASSIGNMENT:
                fields = list(reversed(stmt.val.val.varref.val.fields))
                while len(fields) > 0:
                    field = fields.pop()
                    if field == Accessor.FST or field == Accessor.SND:
                        if type(typ) is AST.TUPLETYPE:
                            if field == Accessor.FST:
                                typ = typ.a.val
                            else:
                                typ = typ.b.val
                        else:
                            ERROR_HANDLER.addError(ERR.IllegalTupleAccessorUsage, [stmt.val.val.varref])
                    elif field == Accessor.HD or field == Accessor.SND:
                        if type(typ) is AST.LISTTYPE:
                            typ = typ.type.val
                        else:
                            ERROR_HANDLER.addError(ERR.IllegalListAccessorUsage, [stmt.val.val.varref])
                    else:
                        raise Exception("Unknown accessor encountered: %s " + field)

                _, stmt.val.val.expr = typecheck(stmt.val.val.expr, typ, symbol_table, op_table, builtin_funcs, func)
            else:
                _, stmt.val.val = typecheck(stmt.val.val, typ, symbol_table, op_table, builtin_funcs, func)

        elif type(stmt.val) == AST.IFELSE:
            for b in stmt.val.condbranches:
                if b.expr is not None:
                    _, b.expr = typecheck(b.expr, ast_boolnode, symbol_table, op_table, builtin_funcs, func)
                stmts.extend(list(reversed(b.stmts)))
        elif type(stmt.val) == AST.LOOP:
            _, stmt.val.cond = typecheck(stmt.val.cond, ast_boolnode, symbol_table, op_table, builtin_funcs, func)
            stmts.extend(list(reversed(stmt.val.stmts)))
        elif type(stmt.val) == AST.RETURN:
            _, stmt.val.expr = typecheck(stmt.val.expr, func['type'].to_type.val, symbol_table, op_table, builtin_funcs, func)
            pass

def typecheck_functions(symbol_table, op_table, builtin_funcs):
    for f in symbol_table.functions:
        for o in symbol_table.functions[f]:
            typecheck_stmts(o, symbol_table, op_table, builtin_funcs)

def typecheck_globals(symbol_table, op_table):
    for g in symbol_table.global_vars:
        _, symbol_table.global_vars[g].expr = typecheck(symbol_table.global_vars[g].expr, symbol_table.global_vars[g].type.val, symbol_table, op_table)