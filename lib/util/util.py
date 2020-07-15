#!/usr/bin/env python3

from io import SEEK_SET
from lib.datastructure.token import Token
from lib.datastructure.AST import AST

'''
class Node():
    def __init__(self, pos, token, children):
        self.token    = token
        self.children = list(children)
'''

def selectiveApply(typ, node, f):
    if type(node) is typ:
        return f(node)
    return node

def treemap(ast, f, replace=True):
    def unpack(val, f):
        if type(val) == list:
            mapped_list = []
            for el in val:
                mapped_list.append(unpack(el, f))
            return mapped_list
        elif type(val) in AST.nodes:# Require enumlike construct for AST
            return treemap(val, f, replace)
        else:
            return val

    if replace:
        ast = f(ast)
    else:
        f(ast)
    if type(ast) is not Token:
        # TODO: Is this really a correct solution?
        if type(ast) is list:
            res = []
            for x in ast:
                res.append(unpack(x, f))
            ast = res
        elif type(ast) in AST.nodes:
            for attr in ast.items():
                ast[attr[0]] = unpack(attr[1], f)
        else:
            raise Exception("Tried to treemap on ",type(ast),ast)

    return ast

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
    offset = position.col - 1
    tabcount = string[:offset].count('\t')
    spacecount = offset - tabcount
    output = "line {}, col {}\n{}\n{}".format(
        position.line,
        position.col,
        string.rstrip(),
        "\t" * tabcount + " " * spacecount + "^")
    return output
