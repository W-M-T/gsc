#!/usr/bin/env python3

from lexer import tokenize
from parser import *
from semantic_analysis import *

def main():
    from io import StringIO

    testprog = StringIO('''
        
        sum(a, b) :: Int Int -> Int {
            Int a = 5;
            
            return a + b;
        }
        
         sum(a, b) :: Bool Bool -> Bool {
            Int a = 5;
            
            return a + b;
        }
        
    ''')
    tokenstream = tokenize(testprog)
    tokenlist = list(tokenstream)

    parse_res = SPL.parse_strict(tokenlist, testprog)

    ERROR_HANDLER.setSourceMapping(testprog, [])
    symbol_table = buildSymbolTable(parse_res)
    print("Calling checkpoint")
    ERROR_HANDLER.checkpoint()


if __name__ == "__main__":
    main()