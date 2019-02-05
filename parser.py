#!/usr/bin/env python3

TOKEN_VAR
TOKEN_IF
TOKEN_ELIF
TOKEN_ELSE
TOKEN_WHILE
TOKEN_FOR
TOKEN_RETURN
TOKEN_PREFIX
TOKEN_INFIXL
TOKEN_INFIXR
TOKEN_TYPESYN
TOKEN_BOOL
TOKEN_EMPTY_LIST
TOKEN_CHAR
TOKEN_INT
TOKEN_TYPE_VOID
TOKEN_TYPE_INT
TOKEN_TYPE_BOOL
TOKEN_TYPE_CHAR
TOKEN_PAR_OPEN
TOKEN_PAR_CLOSE
TOKEN_CURL_OPEN
TOKEN_CURL_CLOSE
TOKEN_BRACK_OPEN
TOKEN_BRACK_CLOSE
TOKEN_ACCESSOR
TOKEN_IDENTIFIER
TOKEN_OP_IDENTIFIER


'''
Zaken als +, -, :, / etc zijn built-in methodes
String is een built-in typesynoniem

TODO
Verplaats datastructuren naar een apart bestand
'''

'''
Lexer heeft string flag
single line comment flag
multiline comment flag
type-of-waarde-context flag (voor -> en , en []), geactiveerd via ::

consumeert keywords als deze niet door iets alfabetisch gevolgd worden

=-teken wordt gewoon gelext als assignment -> dus geen geldige operatornaam
eindigen in comment-mode is error
multiline comment mode sluiten zonder flag is error -> */ geen geldige operatornaam
Vinden van commentsymbolen buiten string mode begint altijd comment
oftewel //* en /* geen geldige operatornamen


'''


class Token():
    def __init__(self, pos, typ, val):
        self.pos = pos
        self.typ = val
        self.val = val


class Position():
    def __init__(self, line, col)
        self.line = line
        self.col  = col


class Node():
    def __init__(self, pos, token, children):
        self.token    = token
        self.children = list(children)