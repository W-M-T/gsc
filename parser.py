#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Token, Node
import parsec as ps

BasicType = ps.token(TOKEN.TYPE_IDENTIFIER, cond=lambda x: x == "Int") # add more

Type = BasicType

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
#        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
#        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    TypeSyn.parse(test1)

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

