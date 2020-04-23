#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
    f(a, b) :: Int Int -> Int {
        Int c = 5;
        if(a > 1) {
            return false;
        }
        else {
            return true;
        }
        a = a + 3;
    }
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    x = SPL.parse_strict(tokenlist, testprog)

    analyseFunc(x.decls[0].val)

if __name__ == "__main__":
    main()