#!/usr/bin/env python3

from enum import IntEnum
from io import SEEK_SET

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
    TOKEN.ACCESSOR        : (lambda x  : "(ACC){}".format(x.val)),
    TOKEN.IDENTIFIER      : (lambda x  : "(ID){}".format(x.val)),
    TOKEN.OP_IDENTIFIER   : (lambda x  : "(OP){}".format(x.val)),
    TOKEN.TYPE_IDENTIFIER : (lambda x  : "(TYPE){}".format(x.val))
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



'''
How to make this O(1):
Read the tokens in byte mode so you can .tell()
Then .decode("utf-8") to use the line
Store a list containing the offsets for each line (or just use the first token that has a new one as a start of the line)
You can use this offset to seek in this function in O(1) given that the file is in byte mode.
'''
def pointToPosition(instream, position): # Could be made O(1) instead of O(n) with some work
    instream.seek(0, SEEK_SET)

    for _ in range(position.line - 1):
        instream.readline()
    line = instream.readline()
    return pointToLine(line, position)

def pointToLine(string, position):
    output = "line {}, col {}\n{}\n{}".format(
        position.line,
        position.col,
        string.rstrip(),
        " " * (position.col - 1) + "^")
    return output
