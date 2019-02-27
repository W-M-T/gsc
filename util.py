#!/usr/bin/env python3

from enum import IntEnum

class TOKEN(IntEnum): # auto() for python >3.5
    VAR             = 1
    IF              = 2
    ELIF            = 3
    ELSE            = 4
    WHILE           = 5
    FOR             = 6
    RETURN          = 7
    PREFIX          = 8
    INFIXL          = 9
    INFIXR          = 10
    TYPESYN         = 11
    BOOL            = 12
    EMPTY_LIST      = 13
    CHAR            = 14
    INT             = 15
    STRING          = 16
    PAR_OPEN        = 17
    PAR_CLOSE       = 18
    CURL_OPEN       = 19
    CURL_CLOSE      = 20
    BRACK_OPEN      = 21
    BRACK_CLOSE     = 22
    SEMICOLON       = 23
    ACCESSOR        = 24
    IDENTIFIER      = 25
    OP_IDENTIFIER   = 26
    TYPE_IDENTIFIER = 27

PRETTY_TOKEN = {
    TOKEN.VAR             : (lambda x  : "var"),
    TOKEN.IF              : (lambda x  : "if"),
    TOKEN.ELIF            : (lambda x  : "elif"),
    TOKEN.ELSE            : (lambda x  : "else"),
    TOKEN.WHILE           : (lambda x  : "while"),
    TOKEN.FOR             : (lambda x  : "for"),
    TOKEN.RETURN          : (lambda x  : "return"),
    TOKEN.PREFIX          : (lambda x  : "prefix"),
    TOKEN.INFIXL          : (lambda x  : "infixl"),
    TOKEN.INFIXR          : (lambda x  : "infixr"),
    TOKEN.TYPESYN         : (lambda x  : "type"),
    TOKEN.BOOL            : (lambda x  : x.val),
    TOKEN.EMPTY_LIST      : (lambda x  : "[]"),
    TOKEN.CHAR            : (lambda x  : "(CHAR){}".format(x.val)),
    TOKEN.INT             : (lambda x  : x.val),
    TOKEN.STRING          : (lambda x  : "(STRING){}".format(x.val)),
    TOKEN.PAR_OPEN        : (lambda x  : "("),
    TOKEN.PAR_CLOSE       : (lambda x  : ")"),
    TOKEN.CURL_OPEN       : (lambda x  : "{"),
    TOKEN.CURL_CLOSE      : (lambda x  : "}"),
    TOKEN.BRACK_OPEN      : (lambda x  : "["),
    TOKEN.BRACK_CLOSE     : (lambda x  : "]"),
    TOKEN.SEMICOLON       : (lambda x  : ";"),
    TOKEN.ACCESSOR        : (lambda x  : x.val),
    TOKEN.IDENTIFIER      : (lambda x  : "(ID){}".format(x.val)),
    TOKEN.OP_IDENTIFIER   : (lambda x  : "(OP){}".format(x.val)),
    TOKEN.TYPE_IDENTIFIER : (lambda x  : x.val)
}

class Token():
    def __init__(self, pos, typ, val):
        self.pos = pos
        self.typ = typ
        self.val = val

    def __str__(self):
        return "<{} @{}{}>".format(self.typ.name, self.pos, ", " + str(self.val) if self.val is not None else "")

    def mini_str(self):
        return "<{}>".format(self.typ.name)

    def pretty(self):
        return PRETTY_TOKEN[self.typ](self)


class Position():
    def __init__(self, line = 1, col = 1):
        self.line = line
        self.col  = col

    def __repr__(self):
        return "line {} :col {}".format(self.line, self.col)

    def copy(self):
        return Position(self.line, self.col)


class Node():
    def __init__(self, pos, token, children):
        self.token    = token
        self.children = list(children)