#!/usr/bin/env python3

from enum import IntEnum
import sys
from lib.datastructure.token import Token
from lib.datastructure.AST import AST
from lib.util.util import pointToPosition
from lib.parser.lexer import REG_FIL
from lib.builtins.functions import ENTRYPOINT_FUNCNAME

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
    # Forbid_illegal_types
    TypeSynVoid = 12
    GlobalVarTypeNone = 13
    GlobalVarVoid = 14
    FunctionTypeNone = 15
    FunctionInputVoid = 16
    FunctionOutputNestedVoid = 17
    LocalVarTypeNone = 18
    LocalVarVoid = 19
    # Typing
    UnsupportedOperandType = 20
    IncompatibleTypes = 21
    UnexpectedType = 22
    UnexpectedTuple = 23
    UndefinedGlobalVar = 24
    UndefinedVar = 25
    NoOverloadedFunDef = 26
    NoOverloadedFunWithArgs = 27
    AmbiguousFunCall = 28
    AmbiguousNestedFunCall = 29
    UndefinedFun = 30
    IllegalTupleAccessorUsage = 31
    UndefinedPrefixOp = 32
    NoOpDefWithType = 33
    NoOpDefWithInputType = 34
    AmbiguousPrefixOp = 35
    InconsistentOpDecl = 36
    DuplicateOpDef = 37
    UnexpectedEmptyList = 38
    IllegalListAccessorUsage = 39
    GlobalDefMustBeConstant = 40
    # Import
    ImportNotFound = 41
    ReservedModuleName = 42
    HeaderFormatIncorrect = 43
    DuplicateImportGlobal = 44
    DuplicateImportType = 45
    DuplicateImportFun = 46
    ImportIdentifierNotFound = 47
    ImportOpIdentifierNotFound = 48
    ImportTypeSynNotFound = 49
    ClashImportGlobal = 50
    ClashImportType = 51
    ImportIdChangeType = 52
    # Compiler / Linker scripts
    CompInputFileExtension = 53
    CompInputFileNonExist = 54
    CompInvalidImportMapping = 55
    CompMalformedObjectFile = 56
    CompInputFileException = 57
    CompOutputFileException = 58
    CompInvalidArguments = 59
    CompModuleFileNameRegex = 60
    # Builtin clashes
    ImportTypeClashBuiltin = 61
    MultipleMain = 62
    WrongMainType = 63
    UndefinedTypeId = 64
    CyclicTypeSyn = 65
    CyclicTypeSynExternal = 66
    #ImportTypeClash = 67
    RecursiveImportNotFound = 68
    MultipleOpIdPropertiesFound = 69
    # Function type clashes
    FuncTypeImportClash = 70
    FuncTypeBuiltinShadow = 71
    FuncTypeBuiltinShadowImport = 72
    FuncTypeLocalClash = 73



ERRMSG = {
    ERR.OverloadFunMultipleDef: 'Overloaded functions "{}" has multiple definitions with the same type:',
    ERR.DuplicateGlobalVarId: 'Duplicate global variable identifier\n{}\nInitial definition:\n{}',
    ERR.ArgCountDoesNotMatchSign: 'Argument count doesn\'t match signature\n{}',
    ERR.DuplicateArgName: 'Duplicate argument name\n{}',
    ERR.DuplicateVarDef: 'Duplicate variable definition\n{}\nInitial definition:\n{}',
    ERR.ReservedTypeId: 'Trying to redefine a reserved type identifier\n{}',
    ERR.DuplicateTypeId: 'Duplicate type identifier\n{}\nInitial definition:\n{}',
    ERR.DuplicateFunDef: 'Overloaded function "{}" has multiple definitions with the same type: {}\n{}',
    ERR.UndefinedOp: 'Operator is not defined:\n{}',
    ERR.BreakOutsideLoop: 'Using a break or continue statement outside of a loop\n{}',
    ERR.NotAllPathsReturn: 'Not all paths in function {} lead to a certain return\n{}',
    ERR.TypeSynVoid: 'Type synonym "{}" cannot contain Void:\n{}',
    ERR.GlobalVarTypeNone: 'Global variable "{}" needs a type:\n{}',
    ERR.GlobalVarVoid: 'Type of global variable "{}" cannot contain Void:\n{}',
    ERR.FunctionTypeNone: 'Function "{}" needs a type:\n{}',
    ERR.FunctionInputVoid: 'Input type of "{}" cannot contain Void:\n{}',
    ERR.FunctionOutputNestedVoid: 'Return type of "{}" contains nested Void:\n{}',
    ERR.LocalVarTypeNone: 'Local variable "{}" of function "{}" needs a type:\n{}',
    ERR.LocalVarVoid: 'Type of local variable "{}" of function "{}" cannot contain Void:\n{}',
    ERR.UnsupportedOperandType: 'Unsupported operand type(s) for {}, expected argument {} to be {}\n{}',
    ERR.IncompatibleTypes: 'Incompatible types: Operator cannot possibly result in {}\n{}',
    ERR.UnexpectedType: 'Unexpected type {}, expected {}\n{}',
    ERR.UnexpectedTuple: 'Unexpected tuple encountered, expected {}\n{}',
    ERR.UndefinedGlobalVar: 'Global Variable {} is not defined\n{}',
    ERR.UndefinedVar: 'Variable {} is not defined\n{}',
    ERR.NoOverloadedFunDef: 'No function definition of {} which results in {}\n{}',
    ERR.NoOverloadedFunWithArgs: 'No function definition of {} which takes the given argument types\n{}',
    ERR.AmbiguousFunCall: 'Ambigious function call, function {} has multiple possible output types\n {}',
    ERR.AmbiguousNestedFunCall: 'Ambigious function call, function {} has multiple possible input types\n {}',
    ERR.UndefinedFun: 'Function {} is not defined\n{}',
    ERR.IllegalTupleAccessorUsage: 'Trying to use tuple accessor on variable that is not a tuple\n{}',
    ERR.UndefinedPrefixOp: 'Prefix operator "{}" is not defined\n{}',
    ERR.NoOpDefWithType: 'No operator definition for "{}" with type {}\n{}',
    ERR.NoOpDefWithInputType: 'No definition of operator "{}" which has the given argument type\n{}',
    ERR.AmbiguousPrefixOp: 'Ambigious usage of prefix operator "{}", multiple matches on given input type\n{}',
    ERR.InconsistentOpDecl: 'Inconsistent declaration of operator {}, fixity and precedence have to be equal to initial definition\n{}',
    ERR.DuplicateOpDef: 'Duplicate operator definition for operator {}, operator with the exact same type was already defined\n{}',
    ERR.UnexpectedEmptyList: 'Unexpected empty list encountered\n{}',
    ERR.IllegalListAccessorUsage: 'Trying to use list accessor on variable that is not a list\n{}',
    ERR.GlobalDefMustBeConstant: 'Global variable definition must be constant\n{}',
    ERR.ImportNotFound: 'Failed to import module: {}\n{}',
    ERR.ReservedModuleName: 'Module name "{}" is a reserved name',
    ERR.HeaderFormatIncorrect: 'Failed to parse headerfile "{}":\n{}',
    ERR.DuplicateImportGlobal: 'Global variable "{}" is imported from multiple modules:{}',
    ERR.DuplicateImportType: 'Type synonym "{}" is imported from multiple modules:{}',
    ERR.DuplicateImportFun: 'Function "{}" is imported from multiple modules:{}',
    ERR.ImportIdentifierNotFound: 'Tried to import an identifier "{}" from module {} that was not found in the headerfile {}',
    ERR.ImportOpIdentifierNotFound: 'Tried to import an operator identifier "{}" from module {} that was not found in the headerfile {}',
    ERR.ImportTypeSynNotFound: 'Tried to import a type identifier "{}" from module {} that was not found in the headerfile {}',
    ERR.ClashImportGlobal: 'Multiple clashing definitions for global variable identifier "{}" in imports:\n{}',
    ERR.ClashImportType: 'Multiple clashing definitions for type identifier "{}" in imports:\n{}',
    ERR.ImportIdChangeType: 'Identifier "{}" aliased to different identifier type:\n{} -> {}\n{}',
    ERR.CompInputFileExtension: 'Input file needs to have extension "{}"',
    ERR.CompInputFileNonExist: 'Input file does not exist: {}',
    ERR.CompInvalidImportMapping: 'Invalid import mapping\nExpecting format:\nLIBNAME:PATH(,LIBNAME:PATH)*\nLIBNAME={}\nPATH=file path not containing ","'.format(REG_FIL.pattern),
    ERR.CompMalformedObjectFile: 'Malformed object file: {}\n{}',
    ERR.CompInputFileException: 'Could not read input file "{}":\n\t{}',
    ERR.CompOutputFileException: 'Could not write to output file "{}":\n\t{}',
    ERR.CompInvalidArguments: 'Invalid arguments:\n{}',
    ERR.CompModuleFileNameRegex: ('Module name "{}" needs to be of format ' + REG_FIL.pattern),
    ERR.ImportTypeClashBuiltin: 'Imported type synonym "{}" conflicts with builtin type',
    ERR.MultipleMain: 'Too many definitions for entrypoint "{}"'.format(ENTRYPOINT_FUNCNAME),
    ERR.WrongMainType: 'Entrypoint ' + ENTRYPOINT_FUNCNAME + ' needs to be of type signature ":: -> Int":\n{}',
    ERR.UndefinedTypeId: 'Type identifier "{}" is not defined:\n{}',
    ERR.CyclicTypeSyn: 'Type synonym "{}" has cyclical definition:\n{}',
    ERR.CyclicTypeSynExternal: 'Imported type synonym "{}" has cyclical definiton:\n{}',
    #ERR.ImportTypeClash: 'Type synonym "{}" clashes with import from module "{}":\n{}',
    ERR.RecursiveImportNotFound: 'Failed to import module header required by dependency: {}\n{}',
    ERR.MultipleOpIdPropertiesFound: 'The infix operator identifier "{}" has ambiguous associativity / precedence:\nFound declarations of the following combinations:\n{}',
    ERR.FuncTypeImportClash: 'There are multiple clashing imports for function "{}"({}) with the same type "{}" from modules "{}" and "{}"',
    ERR.FuncTypeBuiltinShadow: 'Function definition of "{}"({}) has same type "{}" as a builtin function with the same fixity and identifier, which is forbidden: builtins cannot be shadowed:\n{}',
    ERR.FuncTypeBuiltinShadowImport: 'Imported function "{}"({}) has same type "{}" as a builtin function with the same fixity and identifier, which is forbidden: builtins cannot be shadowed',
    ERR.FuncTypeLocalClash: 'There are multiple clashing definitions for function "{}"({}) with the same type "{}":\n{}\n{}'
}

class WARN(IntEnum):
    ShadowGlobalOtherModule = 1
    ShadowFuncOtherModule = 2
    ShadowTypeOtherModule = 3
    ShadowFunArg = 4
    UnreachableStmtBranches = 5
    UnreachableStmtContBreak = 6
    UnreachableStmtReturn = 7
    MultiKindImport = 8
    DuplicateIdSameModuleImport = 9
    DuplicateOpSameModuleImport = 10
    DuplicateTypeSameModuleImport = 11
    ShadowFuncIdType = 12

WARNMSG = {
    WARN.ShadowGlobalOtherModule: 'Shadowing global variable "{}" from module "{}":\n{}',
    WARN.ShadowFuncOtherModule: 'Function ({}) {} with type "{}" was already defined in another module, which is now shadowed', # Unused as of yet
    WARN.ShadowTypeOtherModule: 'Shadowing type synonym "{}" from module "{}":\n{}',
    WARN.ShadowFunArg: 'Shadowing function argument\n{}',
    WARN.UnreachableStmtBranches: 'Statement(s) can never be reached because all preceding branches return.\n{}',
    WARN.UnreachableStmtContBreak: 'Statement(s) can never be reached because of a continue or break statement\n{}',
    WARN.UnreachableStmtReturn: 'Statement(s) can never be reached because of a return\n{}',
    WARN.MultiKindImport: 'Both importall and other imports defined for module "{}":\n{}',
    WARN.DuplicateIdSameModuleImport: 'Multiple imports for the same identifier "{}" from module "{}":\n{}',
    WARN.DuplicateOpSameModuleImport: 'Multiple imports for the same operator identifier "{}" from module "{}":\n{}',
    WARN.DuplicateTypeSameModuleImport: 'Multiple imports for the same type identifier "{}" from module "{}":\n{}',
    WARN.ShadowFuncIdType: 'Local definition of function "{}"({}) shadows import from module "{}" with the same type "{}":\n{}'
}

class ErrorHandler():

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.debug = False
        self.hidewarn = False

    def setSourceMapping(self, sourcecode):
        self.sourcecode = sourcecode

    def addError(self, error_type, tokens, source=None, fatal=False):
        error = {
            'type': error_type,
            'tokens': tokens,
            'source': source
        }
        self.errors.append(error)
        if self.debug or fatal:
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
                info = []
                for t in e['tokens']:
                    if type(t) is Token:
                        info.append(pointToPosition(self.sourcecode, t.pos))
                    elif type(t) in AST.nodes:
                        info.append(pointToPosition(self.sourcecode, t._start_pos))
                    elif type(t) is list and len(t) > 0 and all(map(lambda x: type(x) is Token, t)):
                        info.append("\n".join(map(lambda x: pointToPosition(self.sourcecode, x.pos), t)))
                    elif type(t) is list and len(t) > 0 and all(map(lambda x: type(x) in AST.nodes, t)):
                        info.append("\n".join(map(lambda x: pointToPosition(self.sourcecode, x._start_pos), t)))
                    else:
                        info.append(str(t))
                print(ERRCOLOR.FAIL + "[ERROR] %s" % (ERRMSG[e['type']].format(*info)) + ERRCOLOR.ENDC, file=sys.stderr)

        if not self.hidewarn:
            for w in self.warnings:
                info = []
                for t in w['tokens']:
                    if type(t) is Token:
                        info.append(pointToPosition(self.sourcecode, t.pos))
                    elif type(t) in AST.nodes:
                        info.append(pointToPosition(self.sourcecode, t._start_pos))
                    elif type(t) is list and len(t) > 0 and all(map(lambda x: type(x) is Token, t)):
                        info.append("\n".join(map(lambda x: pointToPosition(self.sourcecode, x.pos), t)))
                    elif type(t) is list and len(t) > 0 and all(map(lambda x: type(x) in AST.nodes, t)):
                        info.append("\n".join(map(lambda x: pointToPosition(self.sourcecode, x._start_pos), t)))
                    else:
                        info.append(str(t))
                print(ERRCOLOR.WARNING + "[WARNING] %s" % (WARNMSG[w['type']].format(*info)) + ERRCOLOR.ENDC, file=sys.stderr)

        if len(self.errors) > 0:
            exit(1)

        self.errors = []
        self.warnings = []


ERROR_HANDLER = ErrorHandler()