#!/usr/bin/env python3

import unittest
import string
import subprocess
import sys
import os

# Makes it possible to import from the lexer
sys.path.insert(0, '../')

from lexer import tokenize
from parser import *

class ParserTester(unittest.TestCase):

    """
    Test all of the parsers. 
    """

    def test_id_parser(self):
        """
        Some examples that should be succesfully parsed
        TODO: Figure out the best way to test whether the parse was succesful.
        """
        tests = [
            [
                Token(None, TOKEN.IDENTIFIER, "test")
            ],        
            [
                Token(None, TOKEN.IDENTIFIER, "test"),
                Token(None, TOKEN.ACCESSOR, ".snd")
            ],        
            [
                Token(None, TOKEN.IDENTIFIER, "test"),
                Token(None, TOKEN.ACCESSOR, ".tl"),
                Token(None, TOKEN.ACCESSOR, ".fst"),
                Token(None, TOKEN.ACCESSOR, ".tl")
            ],        
        ]

        x = 0
        for t in tests:
            with self.subTest():
                print(x)
                res = IdField.parse(t)
                print(res)
                #print("First: " + res[0])
            x += 1

    def test_prefix_op_decl_parser(self):
        pass

    def test_infix_op_decl_parser(self):
        pass

    def test_var_decl_parser(self):
        pass

    def test_basic_type_parser(self):
        pass

    def test_tuple_type_parser(self):
        pass

    def test_list_type_parser(self):
        pass

    def test_type_syn_parser(self):
        pass

    def test_stmtifelse_parser(self):
        pass

    def test_stmtelif_parser(self):
        pass

    def test_stmtelse_parser(self):
        pass

    def test_stmtwhile_parser(self):
        pass

    def test_stmtfor_parser(self):
        pass

    def test_stmtret_parser(self):
        pass

    def test_exp_parser(self):
        pass
             
if __name__ == '__main__':
    unittest.main()
