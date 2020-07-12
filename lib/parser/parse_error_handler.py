#!/usr/bin/env python3

from lib.datastructure.token import TOKEN
from lib.analysis.error_handler import ERRCOLOR

TOKEN_SYNTAX = {
    TOKEN.VAR             : "var",
    TOKEN.IF              : "if",
    TOKEN.ELIF            : "elif",
    TOKEN.ELSE            : "else",
    TOKEN.WHILE           : "while",
    TOKEN.FOR             : "for",
    TOKEN.RETURN          : "return",
    TOKEN.BREAK           : "break",
    TOKEN.CONTINUE        : "continue",
    TOKEN.PREFIX          : "prefix",
    TOKEN.INFIXL          : "infixl",
    TOKEN.INFIXR          : "infixr",
    TOKEN.TYPESYN         : "type",
    TOKEN.BOOL            : "bool",
    TOKEN.EMPTY_LIST      : "[]",
    TOKEN.CHAR            : "char",
    TOKEN.INT             : "int",
    TOKEN.STRING          : "string",
    TOKEN.PAR_OPEN        : "'('",
    TOKEN.PAR_CLOSE       : "')'",
    TOKEN.CURL_OPEN       : "'{'",
    TOKEN.CURL_CLOSE      : "'}'",
    TOKEN.BRACK_OPEN      : "'['",
    TOKEN.BRACK_CLOSE     : "']'",
    TOKEN.SEMICOLON       : "';'",
    TOKEN.COMMA           : "','",
    TOKEN.ACCESSOR        : "Accessor",
    TOKEN.IDENTIFIER      : "Identifier",
    TOKEN.OP_IDENTIFIER   : "Operator",
    TOKEN.TYPE_IDENTIFIER : "Type",
    TOKEN.IMPORT          : "import",
    TOKEN.FROM            : "from",
    TOKEN.AS              : "as",
    TOKEN.FILENAME        : "filename",
    TOKEN.IMPORTALL       : "importall"
}

class ParseErrorHandler():

    def __init__(self):
        self.reset()

    def reset(self):
        self.error_index = -1
        self.error_val = None
        self.error_set = []

    def push_error(self, failure):
        if failure.index > self.error_index:
            self.error_index = failure.index
            self.error_val = failure
            self.error_set = []
        if failure.index >= self.error_index:
            self.error_set.append(failure.expected)

class ParseError(RuntimeError):
    '''Parser error.'''

    def __init__(self, expected, pos):
        super(ParseError, self).__init__() # compatible with Python 2.
        pretty_expected = ', '.join(list(reversed([TOKEN_SYNTAX[x] if x in TOKEN_SYNTAX else x for x in expected])))
        self.expected = pretty_expected
        self.pos = pos

    def __str__(self):
        return ERRCOLOR.FAIL + "[ERROR] A parser exception occurred at {}\nExpected one of the following:\n{}".format(self.pos, self.expected) + ERRCOLOR.ENDC