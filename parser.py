#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Node


def parseTokenStream(instream):
    # obtain expected symbol / rules
    # then pop one from instream, compare

    #print([str(k) for k in list(instream)])
    pass



if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()
    

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

