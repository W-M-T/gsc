#!/usr/bin/env python3

from lib.parser.parser import *
from semantic_analysis import *
from lib.datastructure.AST import *

def main():
    from io import StringIO

    result_trees = []
    #testprog = StringIO()
    with open("./example programs/p1_example.spl") as infile:
        tokenstream = tokenize(infile)

        parse_res = parseTokenStream(tokenstream, infile)
        result_trees.append(parse_res)

        for i in range(10):
            inp = StringIO(printAST(parse_res))
            tokenstream = tokenize(inp)
            parse_res = parseTokenStream(tokenstream, inp)
            result_trees.append(parse_res)

        for el1 in result_trees:
            for el2 in result_trees:
                print(AST.equalVals(el1,el2))
           
           # print(printAST(el))

if __name__ == "__main__":
    main()