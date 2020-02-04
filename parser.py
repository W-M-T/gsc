#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Token, Node
import parsec as ps

# Evaluate return types

@ps.generate
def BasicType():
    a = yield ps.token(TOKEN.TYPE_IDENTIFIER, cond=lambda x: x == "Char") # add more
    return "Char"

@ps.generate
def TupType():
    yield ps.token(TOKEN.PAR_OPEN)
    a = ps.token(TOKEN.TYPE_IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    b = ps.token(TOKEN.TYPE_IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    return (a,b)


@ps.generate
def ListType():
    yield ps.token(TOKEN.BRACK_OPEN)
    a = yield Type
    yield ps.token(TOKEN.BRACK_CLOSE)
    return [a]

'''
@ps.generate
def Type():
    a = BasicType | TupType #| ListType | ps.token(TOKEN.TYPE_IDENTIFIER)
    return a
'''
Type = BasicType | TupType | ListType

@ps.generate
def TypeSyn():
    yield ps.token(TOKEN.TYPESYN)
    identifier = yield ps.token(TOKEN.TYPE_IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=lambda x: x == '=')
    other_type = yield Type
    return (identifier, other_type)






def parseTokenStream(instream):

    pass



if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()
    

    test1 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        
    ]
    test2 = [
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    test3 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    TypeSyn.parse(test3)

    exit()

    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        parseTokenStream(tokenstream)
        '''
        tokenlist = list(tokenstream)
        import random
        randtoken = random.choice(tokenlist)
        print(randtoken)
        print(pointToPosition(infile, randtoken.pos))
        '''

    print("DONE")

