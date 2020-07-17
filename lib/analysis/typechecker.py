#!/usr/bin/env python3

from lib.parser.parser import Accessor_lookup
from lib.datastructure.position import Position
from lib.datastructure.token import Token, TOKEN
from lib.datastructure.AST import AST, FunKind, FunKindToUniq, FunUniq, Accessor
from lib.datastructure.scope import NONGLOBALSCOPE
from lib.debug.AST_prettyprinter import subprint_type
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

''' Type check the given expression '''
def typecheck(expr, exp_type, symbol_table, ext_table, func=None, r=0, noErrors=False):

    if type(expr) is Token:
        if expr.typ == TOKEN.EMPTY_LIST:
            if type(exp_type) == AST.LISTTYPE:
                return True, expr
            else:
                ERROR_HANDLER.addError(ERR.UnexpectedEmptyList, [expr])

        typ = tokenToNode(expr)
        if not AST.equalVals(typ, exp_type):
            if r == 0 and not noErrors:
                ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
            return False, expr

        return True, expr
    elif type(expr) is AST.PARSEDEXPR:
        return typecheck(expr.val, exp_type, symbol_table, ext_table, func, r, noErrors)
    elif type(expr) is AST.RES_VARREF:
        if type(expr.val) is AST.RES_GLOBAL:
            if expr.val.module is None:
                typ = symbol_table.global_vars[expr.val.id.val].type.val
            else:
                typ = ext_table.global_vars[expr.val.id.val]['type'].val
            fields = list(reversed(expr.val.fields))

            success, typ = getSubType(typ, fields, expr)

            if not success:
                return True, expr

            if not AST.equalVals(typ, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
                return False, expr

        elif type(expr.val) is AST.RES_NONGLOBAL:
            typ = None
            if expr.val.scope == NONGLOBALSCOPE.LocalVar:
                typ = func['local_vars'][expr.val.id.val].type.val
            else:
                typ = func['arg_vars'][expr.val.id.val]['type'].val

            fields = list(reversed(expr.val.fields))
            success, typ = getSubType(typ, fields, expr)

            if not success:
                return True, expr

            if not AST.equalVals(typ, exp_type):
                if r == 0 and not noErrors:
                    ERROR_HANDLER.addError(ERR.UnexpectedType, [subprint_type(typ), subprint_type(exp_type), expr])
                return False, expr

        return True, expr
    elif type(expr) is AST.FUNCALL:
        identifier = (FunKindToUniq(expr.kind), expr.id.val)
        if identifier not in symbol_table.functions and identifier not in ext_table.functions:
            ERROR_HANDLER.addError(ERR.UndefinedFun, [expr.id.val, expr.id])
            return True, expr

        # Symbol table functions
        matches = []
        if identifier in symbol_table.functions:
            out_type_matches = {}
            i = 0
            for o in symbol_table.functions[identifier]:
                if AST.equalVals(exp_type, o['type'].to_type.val) or exp_type is None:
                    out_type_matches[i] = o
                i += 1

            for k, o in out_type_matches.items():
                args = []

                if len(o['type'].from_types) == len(expr.args):
                    input_matches = 0

                    for i in range(len(o['type'].from_types)):
                        typ, arg_res = typecheck(expr.args[i], o['type'].from_types[i].val, symbol_table, ext_table, func, r, noErrors=True)
                        args.append(arg_res)
                        if typ:
                            input_matches += 1

                    if input_matches == len(expr.args):
                        matches.append({
                            'id': k,
                            'module': None,
                            'args': args,
                            'returns': not AST.equalVals(o['type'].to_type, AST.TYPE(val=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Void"))),
                        })

        if identifier in ext_table.functions:
            out_type_matches = {}
            i = 0
            for o in ext_table.functions[identifier]:
                if AST.equalVals(exp_type, o['type'].to_type.val) or exp_type is None:
                    if o['module'] not in out_type_matches:
                        out_type_matches[o['module']] = {}
                    out_type_matches[o['module']][i] = o
                i += 1

            if len(out_type_matches) == 0 and len(matches) == 0:
                if not noErrors and exp_type is not None:
                    if expr.kind == FunKind.FUNC:
                        ERROR_HANDLER.addError(ERR.NoOverloadedFunDef, [expr.id.val, subprint_type(exp_type), expr.id])
                    else:
                        ERROR_HANDLER.addError(ERR.NoOpDefWithType, [expr.id.val, subprint_type(exp_type), expr.id])
                return False, expr

            for module, f in out_type_matches.items():
                for oid, of in f.items():
                    args = []
                    if len(of['type'].from_types) == len(expr.args):
                        input_matches = 0

                        for i in range(len(of['type'].from_types)):
                            typ, arg_res = typecheck(expr.args[i], of['type'].from_types[i].val, symbol_table, ext_table, func, r, noErrors=True)
                            args.append(arg_res)
                            if typ:
                                input_matches += 1

                        if input_matches == len(expr.args):
                            matches.append({
                                'id': oid,
                                'module': module,
                                'args': args,
                                'returns': not AST.equalVals(of['type'].to_type, AST.TYPE(val=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Void"))),
                            })

        # Give preference to functions defined in current module if type is exactly the same.
        if len(matches) > 0:
            current_module_matches = 0
            prefered_match = None
            for m in matches:
                if m['module'] is None:
                    current_module_matches += 1
                    if current_module_matches > 1:
                        break
                    else:
                        prefered_match = m

            if current_module_matches == 1:
                matches = [prefered_match]

        if len(matches) == 0:
            if not noErrors:
                if expr.kind == FunKind.FUNC:
                    ERROR_HANDLER.addError(ERR.NoOverloadedFunWithArgs, [expr.id.val, expr.id])
                else:
                    ERROR_HANDLER.addError(ERR.NoOpDefWithInputType, [expr.id.val, expr.id])
            return False, expr
        elif len(matches) > 1 and exp_type is None:
            if not noErrors:
                if expr.kind == FunKind.FUNC:
                    ERROR_HANDLER.addError(ERR.AmbiguousFunCall, [expr.id.val, expr.id])
                else:
                    ERROR_HANDLER.addError(ERR.AmbiguousOp, [expr.id.val, expr.id])
            return False, expr
        elif len(matches) > 1:
            if not noErrors:
                if expr.kind == FunKind.FUNC:
                    ERROR_HANDLER.addError(ERR.AmbiguousNestedFunCall, [expr.id.val, expr.id])
                else:
                    ERROR_HANDLER.addError(ERR.AmbiguousOp, [expr.id.val, expr.id])
            return False, expr
        else:
            if func is None and (matches[0]['module'] != 'builtins' or expr.kind == FunKind.FUNC):
                ERROR_HANDLER.addError(ERR.GlobalDefMustBeConstant, [expr.id])
                return True, expr

        return True, AST.TYPED_FUNCALL(id=expr.id, uniq=FunKindToUniq(expr.kind), args=matches[0]['args'], oid=matches[0]['id'],
                                           module=matches[0]['module'], returns=matches[0]['returns'])

    elif type(expr) is AST.TUPLE:
        if type(exp_type) is not AST.TUPLETYPE:
            ERROR_HANDLER.addError(ERR.UnexpectedTuple, [exp_type.type_id.val, expr])
            return True, expr

        type1, a = typecheck(expr.a, exp_type.a.val, symbol_table, ext_table, func)
        type2, b = typecheck(expr.b, exp_type.b.val, symbol_table, ext_table, func)

        return type1 or type2, AST.TUPLE(a=a, b=b)

    else:
        print(expr)
        print(type(expr))
        raise Exception('Unknown type of expression encountered in typechecking')

def getSubType(typ, fields, expr):
    success = True
    while len(fields) > 0:
        field = fields.pop()
        if Accessor_lookup[field.val] == Accessor.FST or Accessor_lookup[field.val]  == Accessor.SND:
            if type(typ) is AST.TUPLETYPE:
                if Accessor_lookup[field.val] == Accessor.FST:
                    typ = typ.a.val
                else:
                    typ = typ.b.val
            else:
                ERROR_HANDLER.addError(ERR.IllegalTupleAccessorUsage, [field])
                success = False
        elif Accessor_lookup[field.val] == Accessor.HD or Accessor_lookup[field.val] == Accessor.TL:
            # TODO: Check if this is not restrictive
            if type(typ) is AST.LISTTYPE:
                if Accessor_lookup[field.val] == Accessor.HD:
                    if type(typ) is AST.LISTTYPE:
                        typ = typ.type.val
                    else:
                        ERROR_HANDLER.addError(ERR.IllegalListAccessorUsage, [field])
            else:
                ERROR_HANDLER.addError(ERR.IllegalListAccessorUsage, [field])
        else:
            raise Exception("Unknown accessor encountered: %s " + field.val)

    return success, typ

def typecheck_actstmt(stmt, symbol_table, ext_table, func):
    typ = None
    if hasattr(stmt.val, 'varref'):
        if type(stmt.val.varref.val) == AST.RES_NONGLOBAL:
            if stmt.val.varref.val.scope == NONGLOBALSCOPE.LocalVar:
                typ = func['local_vars'][stmt.val.varref.val.id.val].type.val
            else:
                typ = func['arg_vars'][stmt.val.varref.val.id.val]['type'].val
        else:
            if stmt.val.varref.val.module is None:
                typ = symbol_table.global_vars[stmt.val.varref.val.id.val].type.val
            else:
                typ = ext_table.global_vars[stmt.val.varref.val.id.val]['type'].val

    if type(stmt.val) == AST.ASSIGNMENT:
        fields = list(reversed(stmt.val.varref.val.fields))
        success, typ = getSubType(typ, fields, stmt.val.varref)

        if success:
            _, stmt.val.expr = typecheck(stmt.val.expr, typ, symbol_table, ext_table, func)
    else:
        _, stmt.val = typecheck(stmt.val, typ, symbol_table, ext_table, func)

def typecheck_stmts(func, symbol_table, ext_table):
    for vardecl in func['def'].vardecls:
        _, vardecl.expr = typecheck(vardecl.expr, vardecl.type.val, symbol_table, ext_table, func)

    stmts = list(reversed(func['def'].stmts))
    ast_boolnode = AST.BASICTYPE(type_id=Token(Position(), TOKEN.TYPE_IDENTIFIER, "Bool"))
    while len(stmts) > 0:
        stmt = stmts.pop()
        if type(stmt.val) == AST.ACTSTMT:
            typecheck_actstmt(stmt.val, symbol_table, ext_table, func)
        elif type(stmt.val) == AST.IFELSE:
            for b in stmt.val.condbranches:
                if b.expr is not None:
                    _, b.expr = typecheck(b.expr, ast_boolnode, symbol_table, ext_table, func)
                stmts.extend(list(reversed(b.stmts)))
        elif type(stmt.val) == AST.LOOP:
            if stmt.val.cond is not None:
                _, stmt.val.cond = typecheck(stmt.val.cond, ast_boolnode, symbol_table, ext_table, func)
            if stmt.val.init is not None:
                typecheck_actstmt(stmt.val.init, symbol_table, ext_table, func)
            if stmt.val.update is not None:
                typecheck_actstmt(stmt.val.update, symbol_table, ext_table, func)
            stmts.extend(list(reversed(stmt.val.stmts)))
        elif type(stmt.val) == AST.RETURN:
            if stmt.val.expr is not None:
                _, stmt.val.expr = typecheck(stmt.val.expr, func['type'].to_type.val, symbol_table, ext_table, func)

def typecheck_functions(symbol_table, ext_table):
    for f in symbol_table.functions:
        for o in symbol_table.functions[f]:
            typecheck_stmts(o, symbol_table, ext_table)

def typecheck_globals(symbol_table, ext_table):
    for g in symbol_table.global_vars:
        _, symbol_table.global_vars[g].expr = typecheck(symbol_table.global_vars[g].expr, symbol_table.global_vars[g].type.val, symbol_table, ext_table)