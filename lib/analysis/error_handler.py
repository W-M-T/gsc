#!/usr/bin/env python3

from enum import IntEnum
from util import pointToPosition, Token

class ERRCOLOR:
    WARNING = '\033[33m'
    FAIL = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

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
    # forbid_illegal_types
    TypeSynVoid = 12
    GlobalVarTypeNone = 13
    GlobalVarVoid = 14
    FunctionTypeNone = 15
    FunctionInputVoid = 16
    FunctionOutputNestedVoid = 17
    LocalVarTypeNone = 18
    LocalVarVoid = 19
    # Typing
    UnsupportedOperandType = 20,
    IncompatibleTypes = 21,


ERRMSG = {
    ERR.OverloadFunMultipleDef: 'Overloaded functions "{}" has multiple definitions with the same type:',
    ERR.DuplicateGlobalVarId: 'Global variable identifier already used\n{}\nInitial definition:\n{}',
    ERR.ArgCountDoesNotMatchSign: 'Argument count doesn\'t match signature\n{}',
    ERR.DuplicateArgName: 'Duplicate argument name\n{}',
    ERR.DuplicateVarDef: 'Duplicate variable definition\n{}\nInitial definition:\n{}',
    ERR.ReservedTypeId: 'Trying to redefine a reserved type identifier\n{}',
    ERR.DuplicateTypeId: 'Type identifier already defined\n{}',#\nInitial definition:\n{} This one doesn't work well enough yet: doesn't point to the type definition
    ERR.DuplicateFunDef: 'Overloaded function "{}" has multiple definitions with the same type: {}\n{}',
    ERR.UndefinedOp: 'Operator is not defined\n{}',
    ERR.BreakOutsideLoop: 'Using a break or continue statement outside of a loop',
    ERR.NotAllPathsReturn: 'Not all paths in function {} lead to a certain return\n{}',
    ERR.TypeSynVoid: 'Type synonym {} cannot have Void in its type',
    ERR.GlobalVarTypeNone: 'Global var {} needs a type',
    ERR.GlobalVarVoid: 'Global variable {} cannot have Void in its type',
    ERR.FunctionTypeNone: 'Function {} needs a type',
    ERR.FunctionInputVoid: 'Input type of {} cannot contain Void',
    ERR.FunctionOutputNestedVoid: 'Return type of {} contains nested Void',
    ERR.LocalVarTypeNone: 'Local variable {} of function {} needs a type',
    ERR.LocalVarVoid: 'Variable {} of function {} has type containing Void',
    ERR.UnsupportedOperandType: 'Unsupported operand type(s) for {}: "{}" and "{}"\n{}',
    ERR.IncompatibleTypes: 'Incompatible types: Operator cannot possible result in {}\n{}'
}

class WARN(IntEnum):
    ShadowVarOtherModule = 1
    ShadowFunArg = 2
    UnreachableStmtBranches = 3
    UnreachableStmtContBreak = 4
    UnreachableStmtReturn = 5

WARNMSG = {
    WARN.ShadowVarOtherModule: 'This variable was already defined in another module, which is now shadowed.',
    WARN.ShadowFunArg: 'Shadowing function argument\n{}',
    WARN.UnreachableStmtBranches: 'The statements can never be reached because all branches return.\n{}',
    WARN.UnreachableStmtContBreak: 'The statements can never be reached because of a continue or break statement',
    WARN.UnreachableStmtReturn: 'Statement(s) can never be reached because of a return.\n{}'
}

class ErrorHandler():

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.debug = False
        self.hidewarn = False

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
        if self.debug:
            self.checkpoint()

    def addWarning(self, warning_type, tokens, source=None):
        warning = {
            'type': warning_type,
            'tokens': tokens,
            'source': source
        }
        self.warnings.append(warning)
        if self.debug:
            self.checkpoint()

    def checkpoint(self):
        if len(self.errors) > 0:
            for e in self.errors:
                info = [pointToPosition(self.sourcecode, t.pos) if type(t) is Token else str(t) for t in e['tokens']]
                print(ERRCOLOR.FAIL + "[ERROR] %s" % (ERRMSG[e['type']].format(*info)) + ERRCOLOR.ENDC)

        if not self.hidewarn:
            for w in self.warnings:
                info = [pointToPosition(self.sourcecode, t.pos) if type(t) is Token else str(t) for t in w['tokens']]
                print(ERRCOLOR.WARNING + "[WARNING] %s" % (WARNMSG[w['type']].format(*info)) + ERRCOLOR.ENDC)

        if len(self.errors) > 0:
            exit(1)

        self.errors = []
        self.warnings = []


ERROR_HANDLER = ErrorHandler()