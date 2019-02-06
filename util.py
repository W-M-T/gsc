#!/usr/bin/env python3

from enum import IntEnum

class TOKEN(IntEnum): # auto() for python >3.5
    VAR           = 1
    IF            = 2
    ELIF          = 3
    ELSE          = 4
    WHILE         = 5
    FOR           = 6
    RETURN        = 7
    PREFIX        = 8
    INFIXL        = 9
    INFIXR        = 10
    TYPESYN       = 11
    BOOL          = 12
    EMPTY_LIST    = 13
    CHAR          = 14
    INT           = 15
    TYPE_VOID     = 16
    TYPE_INT      = 17
    TYPE_BOOL     = 18
    TYPE_CHAR     = 19
    PAR_OPEN      = 20
    PAR_CLOSE     = 21
    CURL_OPEN     = 22
    CURL_CLOSE    = 23
    BRACK_OPEN    = 24
    BRACK_CLOSE   = 25
    ACCESSOR      = 26
    IDENTIFIER    = 27
    OP_IDENTIFIER = 28


class Token():
    def __init__(self, pos, typ, val):
        self.pos = pos
        self.typ = typ
        self.val = val


class Position():
    def __init__(self, line = 1, col = 1):
        self.line = line
        self.col  = col


class Node():
    def __init__(self, pos, token, children):
        self.token    = token
        self.children = list(children)