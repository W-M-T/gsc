#!/usr/bin/env python3


class Position():
    def __init__(self, line, col)
        self.line = line
        self.col  = col

class Node():
    def __init__(self, pos, token, children):
        self.pos      = pos
        self.token    = token
        self.children = list(children)