#!/usr/bin/env python3

from enum import IntEnum
from util import pointToPosition

class ERR(IntEnum):
    OverloadFunMultipleDef = 1
    DuplicateGlobalVarId = 2
    ArgCountDoesNotMatchSign = 3
    DuplicateArgName = 4
    DuplicateVarDef = 5
    DuplicateFunDef = 6
    ReservedTypeId = 7
    DuplicateTypeId = 8
    UndefinedOp = 9
    BreakOutsideLoop = 10
    NotAllPathsReturn = 11

ERRMSG = {
    ERR.OverloadFunMultipleDef: 'Overloaded functions "{}" has multiple definitions with the same type:',
    ERR.DuplicateGlobalVarId: 'Global variable identifier already used\n {} \nInitial definition:\n {}',
    ERR.ArgCountDoesNotMatchSign: 'Argument count doesn\'t match signature {}',
    ERR.DuplicateArgName: 'Duplicate argument name {}',
    ERR.DuplicateVarDef: 'Duplicate variable definition\n {} \nInitial definition:\n {}',
    ERR.ReservedTypeId: 'Trying to redefine a reserved type identifier\n {}',
    ERR.DuplicateTypeId: 'Type identifier already defined\n {}',
    ERR.DuplicateFunDef: 'Overloaded function "{}" has multiple definitions with the same type: {} \n {}',
    ERR.UndefinedOp: 'Operator is not defined\n {}',
    ERR.BreakOutsideLoop: 'Using a break or continue statement out of a loop\n {}',
    ERR.NotAllPathsReturn: 'Not all paths lead to a return '
}

class WARN(IntEnum):
    ShadowVarOtherModule = 1
    ShadowFunArg = 2
    UnreachableStmtBranches = 3
    UnreachableStmtContBreak = 4
    UnreachableStmtReturn = 5

WARNMSG = {
    WARN.ShadowVarOtherModule: 'This variable was already defined in another module, which is now shadowed.',
    WARN.ShadowFunArg: 'Shadowing function argument\n {}',
    WARN.UnreachableStmtBranches: 'The statements can never be reached because all branches return.\n {}',
    WARN.UnreachableStmtContBreak: 'The statements can never be reached because of a continue or break statement',
    WARN.UnreachableStmtReturn: 'The statements can never be reached because of a return'
}

class ErrorHandler():

    errors = []
    warnings = []

    def setSourceMapping(self, sourcecode, import_map):
        self.sourcecode = sourcecode
        self.import_map = import_map

    def addError(self, error_type, tokens, source=None):
        error = {
            'type': error_type,
            'tokens': tokens,
            'source': source
        }
        self.errors.append(error)

    def addWarning(self, warning_type, tokens, source=None):
        warning = {
            'type': warning_type,
            'tokens': tokens,
            'source': source
        }
        self.warnings.append(warning)

    def checkpoint(self):
        if len(self.errors) > 0:
            for e in self.errors:
                strings = [pointToPosition(self.sourcecode, t.pos) if type(t) is not str else t for t in e['tokens']]
                print("[ERROR] %s" % (ERRMSG[e['type']].format(*strings)))

        for w in self.warnings:
            strings = [pointToPosition(self.sourcecode, t.pos) if type(t) is not str else t for t in w['tokens']]
            print("[WARNING] %s" % (WARNMSG[w['type']].format(*strings)))

        self.warnings = []


ERROR_HANDLER = ErrorHandler()