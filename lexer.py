#!/usr/bin/env python3

import time
import sys
import re

from util import TOKEN, Token, Position

# Constants

KEYWORDS = {
    "var"    : TOKEN.VAR,
    "if"     : TOKEN.IF,
    "elif"   : TOKEN.ELIF,
    "else"   : TOKEN.ELSE,
    "while"  : TOKEN.WHILE,
    "for"    : TOKEN.FOR,
    "return" : TOKEN.RETURN,
    "prefix" : TOKEN.PREFIX,
    "infixl" : TOKEN.INFIXL,
    "infixr" : TOKEN.INFIXR,
    "type"   : TOKEN.TYPESYN
}
VALUES = {
    "True"  : TOKEN.BOOL,
    "False" : TOKEN.BOOL,
    "[]"    : TOKEN.EMPTY_LIST
}
TYPES = {
    "Void" : TOKEN.TYPE_VOID,
    "Int"  : TOKEN.TYPE_INT,
    "Bool" : TOKEN.TYPE_BOOL,
    "Char" : TOKEN.TYPE_CHAR
}
ACCESSORS = {
    ".hd"  : TOKEN.ACCESSOR,
    ".tl"  : TOKEN.ACCESSOR,
    ".fst" : TOKEN.ACCESSOR,
    ".snd" : TOKEN.ACCESSOR,
}

# Regexes (need to be checked)

REG_ID  = re.compile("[a-z][a-z_]*")
REG_OP  = re.compile("[!#$%&*+/<=>?@\\^|:,~-]+")
REG_INT = re.compile("\\d+")
REG_STR = re.compile("\"([^\0\a\b\f\n\r\t\v\\\'\"]|\\\\[0abfnrtv\\\"\'])+\"")# needs to be tested
REG_CHR = re.compile("\'([^\0\a\b\f\n\r\t\v\\\'\"]|\\\\[0abfnrtv\\\"\'])\'")# needs to be tested
# String and char regexes still missing legal digraph patterns (i.e. no \t char, but \ char followed by t char is allowed)

def tokenize(filename):
    FLAG_STRING         = False
    FLAG_CHAR           = False
    FLAG_MULTI_COMMENT  = False
    FLAG_TYPE_CONTEXT   = False

    pos = Position() # Is it not a problem if this were to get passed by reference?

    yield(Token(pos, TOKEN.TYPE_VOID, "Hello world"))

    with open(filename, "r") as infile:
        curdata = ""
        for line in infile:
            curdata = line
            while len(curdata) > 0:
                curdata = curdata.lstrip()

                # If not in a string or char:

                    # Test for comment

                    # Test for keyword tokens

                    # Test for string start

                    # (TODO Distinguish between type / assignment context in logic)


                return




if __name__ == "__main__":
    for t in tokenize("./example programs/p1_example.spl"):
        print(t.typ, end=" ")
        sys.stdout.flush()
        time.sleep(0.1)
    print("end")