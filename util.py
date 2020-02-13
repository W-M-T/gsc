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
    BREAK           = 8
    CONTINUE        = 9
    PREFIX          = 10
    INFIXL          = 11
    INFIXR          = 12
    TYPESYN         = 13
    BOOL            = 14
    EMPTY_LIST      = 15
    CHAR            = 16
    INT             = 17
    STRING          = 18
    PAR_OPEN        = 19
    PAR_CLOSE       = 20
    CURL_OPEN       = 21
    CURL_CLOSE      = 22
    BRACK_OPEN      = 23
    BRACK_CLOSE     = 24
    SEMICOLON       = 25
    ACCESSOR        = 26
    IDENTIFIER      = 27
    OP_IDENTIFIER   = 28
    TYPE_IDENTIFIER = 29
    IMPORT          = 30
    FROM            = 31

PRETTY_TOKEN = {
    TOKEN.VAR             : (lambda x : "var"),
    TOKEN.IF              : (lambda x : "if"),
    TOKEN.ELIF            : (lambda x : "elif"),
    TOKEN.ELSE            : (lambda x : "else"),
    TOKEN.WHILE           : (lambda x : "while"),
    TOKEN.FOR             : (lambda x : "for"),
    TOKEN.RETURN          : (lambda x : "return"),
    TOKEN.BREAK           : (lambda x : "break"),
    TOKEN.CONTINUE        : (lambda x : "continue"),
    TOKEN.PREFIX          : (lambda x : "prefix"),
    TOKEN.INFIXL          : (lambda x : "infixl"),
    TOKEN.INFIXR          : (lambda x : "infixr"),
    TOKEN.TYPESYN         : (lambda x : "type"),
    TOKEN.BOOL            : (lambda x : x.val),
    TOKEN.EMPTY_LIST      : (lambda x : "[]"),
    TOKEN.CHAR            : (lambda x : "(CHAR){}".format(x.val)),
    TOKEN.INT             : (lambda x : x.val),
    TOKEN.STRING          : (lambda x : "(STRING){}".format(x.val)),
    TOKEN.PAR_OPEN        : (lambda x : "("),
    TOKEN.PAR_CLOSE       : (lambda x : ")"),
    TOKEN.CURL_OPEN       : (lambda x : "{"),
    TOKEN.CURL_CLOSE      : (lambda x : "}"),
    TOKEN.BRACK_OPEN      : (lambda x : "["),
    TOKEN.BRACK_CLOSE     : (lambda x : "]"),
    TOKEN.SEMICOLON       : (lambda x : ";"),
    TOKEN.ACCESSOR        : (lambda x : "(ACC){}".format(x.val)),
    TOKEN.IDENTIFIER      : (lambda x : "(ID){}".format(x.val)),
    TOKEN.OP_IDENTIFIER   : (lambda x : "(OP){}".format(x.val)),
    TOKEN.TYPE_IDENTIFIER : (lambda x : "(TYPE){}".format(x.val)),
    TOKEN.IMPORT          : (lambda x : "import"),
    TOKEN.FROM            : (lambda x : "from"),
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
