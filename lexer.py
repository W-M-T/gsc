#!/usr/bin/env python3

import sys
import re

from util import TOKEN, Token, Position, pointToLine
'''
TODO
Refactor tokenize along repeating pattern to improve readability
'''

# Constants

KEYWORDS = {
    "var"      : TOKEN.VAR,
    "if"       : TOKEN.IF,
    "elif"     : TOKEN.ELIF,
    "else"     : TOKEN.ELSE,
    "while"    : TOKEN.WHILE,
    "for"      : TOKEN.FOR,
    "return"   : TOKEN.RETURN,
    "break"    : TOKEN.BREAK,
    "continue" : TOKEN.CONTINUE,
    "prefix"   : TOKEN.PREFIX,
    "infixl"   : TOKEN.INFIXL,
    "infixr"   : TOKEN.INFIXR,
    "type"     : TOKEN.TYPESYN,
    "import"   : TOKEN.IMPORT,
    "from"     : TOKEN.FROM,
    "as"       : TOKEN.AS
}
BOOLS = {
    "True"  : TOKEN.BOOL,
    "False" : TOKEN.BOOL,
}
VALUES = {
    **BOOLS,
    "[]"    : TOKEN.EMPTY_LIST,
}
COMBINED_KEYWORDS = {**KEYWORDS, **VALUES}
KEYWORD_LIST = list(COMBINED_KEYWORDS.keys())

SCOPING_SYMBOLS = {
    "("  : TOKEN.PAR_OPEN,
    ")"  : TOKEN.PAR_CLOSE,
    "{"  : TOKEN.CURL_OPEN,
    "}"  : TOKEN.CURL_CLOSE,
    "["  : TOKEN.BRACK_OPEN,
    "]"  : TOKEN.BRACK_CLOSE,
    ";"  : TOKEN.SEMICOLON,
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

REG_ID  = re.compile(r"[a-z][a-zA-Z0-9_]*")
REG_TYP = re.compile(r"[A-Z][a-zA-Z0-9_]*")
REG_OP  = re.compile(r"[!#$%&*+/<=>?@\\\\^|:,~-]+")
REG_INT = re.compile(r"\d+")
REG_STR = re.compile(r"\"([^\0\a\b\f\n\r\t\v\\\'\"]|\\[0abfnrtv\\\"\'])*\"")# needs to be tested
REG_CHR = re.compile(r"\'([^\0\a\b\f\n\r\t\v\\\'\"]|\\[0abfnrtv\\\"\'])\'")# needs to be tested

REG_KEYWORD_END = re.compile(r"[^a-zA-Z0-9]|$")

# Choice: Keywords and value/type literals should be followed by a non-alphanumeric character
# Choice: Accessors cannot be preceded by whitespace
# Choice: Comments are whitespace

# Choice: Keywords cannot be used for identifiers
# Choice: Symbols with meaning in syntax (->, ::, ',', =) are reserved for clarity


def prefix_strip(string, prefix):
    if string.startswith(prefix):
        return (True, string[len(prefix):])
    else:
        return (False, None)

def prefix_keyword(string):
    for keyword in KEYWORD_LIST:
        found, strippeddata = prefix_strip(string, keyword)
        if found and REG_KEYWORD_END.match(strippeddata):
            if keyword in BOOLS:
                return (True, strippeddata, COMBINED_KEYWORDS[keyword], keyword == "True")
            else:
                return (True, strippeddata, COMBINED_KEYWORDS[keyword], None)
    return (False, None, None, None)

def prefix_symbol(string):
    for symbol in SCOPING_SYMBOLS:
        found, strippeddata = prefix_strip(string, symbol)
        if found:
            return (True, strippeddata, SCOPING_SYMBOLS[symbol])
    return (False, None, None)

def prefix_identifier(string):
    tempmatch = REG_ID.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        if REG_KEYWORD_END.match(rest): # Should always happen?
            return (True, rest, TOKEN.IDENTIFIER, found_id)
    tempmatch = REG_TYP.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        if REG_KEYWORD_END.match(rest): # Should always happen?
            return (True, rest, TOKEN.TYPE_IDENTIFIER, found_id)
    return (False, None, None, None)

def prefix_op_identifier(string):
    tempmatch = REG_OP.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        return (True, rest, TOKEN.OP_IDENTIFIER, found_id)
    return (False, None, None, None)

def prefix_val_literal(string): # TODO improve this code
    tempmatch = REG_INT.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        return (True, rest, TOKEN.INT, int(found_id))
    tempmatch = REG_STR.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        return (True, rest, TOKEN.STRING, found_id) 
    tempmatch = REG_CHR.match(string)
    if tempmatch:
        found_id = tempmatch.group(0)
        rest = string[len(found_id):]
        return (True, rest, TOKEN.CHAR, found_id)
    return (False, None, None, None)

def prefix_accessor(string):
    for keyword in ACCESSORS:
        found, strippeddata = prefix_strip(string, keyword)
        if found:
            return (True, strippeddata, TOKEN.ACCESSOR, keyword)
    return (False, None, None)

def tokenize(inputstream):
    FLAG_SKIPPED_WHITESPACE = True
    FLAG_MULTI_COMMENT      = False
    ERRORS_OCCURED          = False

    pos = Position()


    curdata = ""
    for line in inputstream:
        curdata = line

        FLAG_SKIPPED_WHITESPACE = True # Newline is considered whitespace

        while len(curdata) > 0:
            pos.col = len(line) - len(curdata) + 1

            if not FLAG_MULTI_COMMENT: # Not currently in a multiline comment
                # Test for whitespace
                if curdata[0].isspace():
                    curdata = curdata.lstrip()
                    FLAG_SKIPPED_WHITESPACE = True
                    continue

                # Test for single comment
                if curdata.startswith(COMMENT_SINGLE):
                    FLAG_SKIPPED_WHITESPACE = True
                    break # We can discard the entire line from here on

                # Test for multiline comment start
                found, strippeddata = prefix_strip(curdata, COMMENT_START)
                if found:
                    FLAG_SKIPPED_WHITESPACE = True
                    FLAG_MULTI_COMMENT = True
                    # Modify string
                    curdata = strippeddata
                    continue

                # Test for keyword tokens
                found, strippeddata, temptoken, val = prefix_keyword(curdata)
                if found:
                    yield(Token(pos.copy(), temptoken, val))
                    FLAG_SKIPPED_WHITESPACE = False
                    # Modify string
                    curdata = strippeddata
                    continue

                # Test for symbols
                found, strippeddata, temptoken = prefix_symbol(curdata)
                if found:
                    yield(Token(pos.copy(), temptoken, None))
                    FLAG_SKIPPED_WHITESPACE = False
                    # Modify string
                    curdata = strippeddata
                    continue

                # Test for identifiers
                found, strippeddata, temptoken, val = prefix_identifier(curdata)
                if found:
                    yield(Token(pos.copy(), temptoken, val))
                    FLAG_SKIPPED_WHITESPACE = False
                    # Modify string
                    curdata = strippeddata
                    continue

                # Test for operator identifiers
                found, strippeddata, temptoken, val = prefix_op_identifier(curdata)
                if found:
                    yield(Token(pos.copy(), TOKEN.OP_IDENTIFIER, val))
                    FLAG_SKIPPED_WHITESPACE = False
                    # Modify string
                    curdata = strippeddata
                    continue

                # Test for value literal
                found, strippeddata, temptoken, val = prefix_val_literal(curdata)
                if found:
                    yield(Token(pos.copy(), temptoken, val))
                    FLAG_SKIPPED_WHITESPACE = False
                    # Modify string
                    curdata = strippeddata
                    continue

                if not FLAG_SKIPPED_WHITESPACE:
                    found, strippeddata, temptoken, val = prefix_accessor(curdata)
                    if found:
                        yield(Token(pos.copy(), temptoken, val))
                        FLAG_SKIPPED_WHITESPACE = False
                        # Modify data
                        curdata = strippeddata
                        continue



            else:
                # Test for multiline comment end
                found, strippeddata = prefix_strip(curdata, COMMENT_END)
                if found:
                    FLAG_SKIPPED_WHITESPACE = True
                    FLAG_MULTI_COMMENT = False
                    # Modify string
                    curdata = strippeddata
                    continue
                else: # Maybe skip to */ if it exists?
                    curdata = curdata[1:]
                    continue

            sys.stderr.write("Lexing error:\n{}\nInvalid syntax\n\n".format(pointToLine(line, pos)))
            ERRORS_OCCURED = True
            '''
            TODO
            Decide when to halt execution
            Error recovery (while still not compiling) would be desired
            It is already pretty easy to recover to next line by just setting a flag here and halting after the loop
            but we would ideally also recover inside the same line.
            '''
            break

        pos.line += 1

    if ERRORS_OCCURED:
        exit(1)



if __name__ == "__main__":
    from argparse import ArgumentParser
    argparser = ArgumentParser(description="SPL Lexer")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()

    with open(args.infile, "r") as infile:

        cur = None
        
        for t in tokenize(infile):
            if cur is None:
                cur = t.pos.line
            if t.pos.line != cur:
                print()
                cur = t.pos.line
                print(" " * (t.pos.col-1), end="")
            print(t.pretty(), end=" ")
    

        print("\nEND")
        '''
        infile.seek(0,0)
        import json
        with open(args.infile+".json", "w") as outfile:
            outfile.write(json.dumps(list(tokenize(infile)), default = lambda o: o.__dict__, sort_keys=True, indent=4))
        '''
