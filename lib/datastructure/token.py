#!/usr/bin/env python3

from enum import IntEnum

class TOKEN(IntEnum):  # auto() for python >3.5
    VAR = 1
    IF = 2
    ELIF = 3
    ELSE = 4
    WHILE = 5
    FOR = 6
    RETURN = 7
    BREAK = 8
    CONTINUE = 9
    PREFIX = 10
    INFIXL = 11
    INFIXR = 12
    TYPESYN = 13
    BOOL = 14
    EMPTY_LIST = 15
    CHAR = 16
    INT = 17
    STRING = 18
    PAR_OPEN = 19
    PAR_CLOSE = 20
    CURL_OPEN = 21
    CURL_CLOSE = 22
    BRACK_OPEN = 23
    BRACK_CLOSE = 24
    SEMICOLON = 25
    COMMA = 26
    ACCESSOR = 27
    IDENTIFIER = 28
    OP_IDENTIFIER = 29
    TYPE_IDENTIFIER = 30
    IMPORT = 31
    FROM = 32
    AS = 33
    FILENAME = 34
    IMPORTALL = 35


PRETTY_TOKEN = {
    TOKEN.VAR: (lambda x: "var"),
    TOKEN.IF: (lambda x: "if"),
    TOKEN.ELIF: (lambda x: "elif"),
    TOKEN.ELSE: (lambda x: "else"),
    TOKEN.WHILE: (lambda x: "while"),
    TOKEN.FOR: (lambda x: "for"),
    TOKEN.RETURN: (lambda x: "return"),
    TOKEN.BREAK: (lambda x: "break"),
    TOKEN.CONTINUE: (lambda x: "continue"),
    TOKEN.PREFIX: (lambda x: "prefix"),
    TOKEN.INFIXL: (lambda x: "infixl"),
    TOKEN.INFIXR: (lambda x: "infixr"),
    TOKEN.TYPESYN: (lambda x: "type"),
    TOKEN.BOOL: (lambda x: str(x.val)),
    TOKEN.EMPTY_LIST: (lambda x: "[]"),
    TOKEN.CHAR: (lambda x: "(CHAR){}".format(x.val)),
    TOKEN.INT: (lambda x: str(x.val)),
    TOKEN.STRING: (lambda x: "(STRING){}".format(x.val)),
    TOKEN.PAR_OPEN: (lambda x: "("),
    TOKEN.PAR_CLOSE: (lambda x: ")"),
    TOKEN.CURL_OPEN: (lambda x: "{"),
    TOKEN.CURL_CLOSE: (lambda x: "}"),
    TOKEN.BRACK_OPEN: (lambda x: "["),
    TOKEN.BRACK_CLOSE: (lambda x: "]"),
    TOKEN.SEMICOLON: (lambda x: ";"),
    TOKEN.COMMA: (lambda x: ","),
    TOKEN.ACCESSOR: (lambda x: "(ACC){}".format(x.val)),
    TOKEN.IDENTIFIER: (lambda x: "(ID){}".format(x.val)),
    TOKEN.OP_IDENTIFIER: (lambda x: "(OP){}".format(x.val)),
    TOKEN.TYPE_IDENTIFIER: (lambda x: "(TYPE){}".format(x.val)),
    TOKEN.IMPORT: (lambda x: "import"),
    TOKEN.FROM: (lambda x: "from"),
    TOKEN.AS: (lambda x: "as"),
    TOKEN.FILENAME: (lambda x: "(FILENAME){}".format(x.val)),
    TOKEN.IMPORTALL: (lambda x: "importall")
}


class Token():
    def __init__(self, pos, typ, val):
        self.pos = pos
        self.typ = typ
        self.val = val

    def __str__(self):
        return "<{} @{}{}>".format(self.typ.name, self.pos, ", " + str(self.val) if self.val is not None else "")

    def __repr__(self):
        return self.pretty()

    def mini_str(self):
        return "<{}>".format(self.typ.name)

    def pretty(self):
        return PRETTY_TOKEN[self.typ](self)
