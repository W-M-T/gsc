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
COMBINED_KEYWORDS = {**KEYWORDS, **VALUES, **TYPES}

SYMBOLS = {
    "("  : TOKEN.PAR_OPEN,
    ")"  : TOKEN.PAR_CLOSE,
    "{"  : TOKEN.CURL_OPEN,
    "}"  : TOKEN.CURL_CLOSE,
    "["  : TOKEN.BRACK_OPEN,
    "]"  : TOKEN.BRACK_CLOSE,
    ";"  : TOKEN.SEMICOLON,
    "::" : TOKEN.TYPE_SIG,
    "="  : TOKEN.ASSIGNMENT,
    "->" : TOKEN.ARROW,
    ","  : TOKEN.TYPE_COMMA

}
ACCESSORS = {
    ".hd"  : TOKEN.ACCESSOR,
    ".tl"  : TOKEN.ACCESSOR,
    ".fst" : TOKEN.ACCESSOR,
    ".snd" : TOKEN.ACCESSOR,
}
COMMENT_SINGLE = "//"
COMMENT_START  = "/*"
COMMENT_END    = "*/"


# Regexes (need to be checked)

REG_ID  = re.compile("[a-z][a-z_]*")
REG_OP  = re.compile("[!#$%&*+/<=>?@\\^|:,~-]+")
REG_INT = re.compile("\\d+")
REG_STR = re.compile("\"([^\0\a\b\f\n\r\t\v\\\'\"]|\\\\[0abfnrtv\\\"\'])+\"")# needs to be tested
REG_CHR = re.compile("\'([^\0\a\b\f\n\r\t\v\\\'\"]|\\\\[0abfnrtv\\\"\'])\'")# needs to be tested

REG_KEY_END = re.compile("[^a-zA-Z0-9]|$")

# Choice: Keywords and value/type literals should be followed by a non-alphanumeric character
# Choice: Accessors cannot be preceded by whitespace
# Choice: Comments are whitespace

def tokenize(filename):
    FLAG_SKIPPED_WHITESPACE = True
    FLAG_MULTI_COMMENT      = False
    FLAG_TYPE_CONTEXT       = False

    pos = Position() # Is it not a problem if this were to get passed by reference?

    yield(Token(pos, TOKEN.TYPE_VOID, "Hello world"))

    with open(filename, "r") as infile:
        curdata = ""
        for line in infile:
            curdata = line

            FLAG_SKIPPED_WHITESPACE = True # Newline is considered whitespace

            while len(curdata) > 0:
                pos.col = len(line) - len(curdata)

                # Test for whitespace
                if False:
                    curdata = curdata.lstrip()
                    FLAG_SKIPPED_WHITESPACE = True
                    continue

                # Test for single comment
                if False:
                    FLAG_SKIPPED_WHITESPACE = True
                    break

                # Test for multiline start
                if False:
                    FLAG_SKIPPED_WHITESPACE = True
                    FLAG_MULTI_COMMENT = True
                    # Modify string
                    continue

                # Test for multiline end
                if False:
                    FLAG_SKIPPED_WHITESPACE = True
                    FLAG_MULTI_COMMENT = False
                    #Modify string
                    continue

                # Test for keyword tokens
                if False:
                    tempmatch = ""
                    temptoken = COMBINED_KEYWORDS[tempmatch]
                    yield(Token(deepcopy(pos), temptoken, None))
                    FLAG_SKIPPED_WHITESPACE = False
                    continue

                # (TODO Distinguish between type / assignment context in logic)


                return

            pos.line += 1



if __name__ == "__main__":
    for t in tokenize("./example programs/debug.spl"):
        print(t, end=" ")
    print()
    '''
    for t in tokenize("./example programs/p1_example.spl"):
        print(t.typ, end=" ")
        sys.stdout.flush()
        time.sleep(0.1)
    print("end")
    '''