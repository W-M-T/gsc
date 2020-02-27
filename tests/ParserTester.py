#!/usr/bin/env python3

import sys
import unittest

# Makes it possible to import from the lexer
sys.path.insert(0, '../')

from parser import *

class ParserTester(unittest.TestCase):

    """
    Test all of the parsing functions.
    Every test get a list of tokens as input rather than actual SPL source code
    since the goal is to test the parsing step instead of both the lexer and the parser.
    """

    def test_id_parser(self):

        # Validate parsing of an identifier.

        tests = [
            [
                # Basic identifier
                Token(None, TOKEN.IDENTIFIER, "test")
            ],
            [
                # Indentifier with one accessor
                Token(None, TOKEN.IDENTIFIER, "test"),
                Token(None, TOKEN.ACCESSOR, ".snd")
            ],
            [
                # Identifier with multiple different accessors
                Token(None, TOKEN.IDENTIFIER, "test"),
                Token(None, TOKEN.ACCESSOR, ".tl"),
                Token(None, TOKEN.ACCESSOR, ".snd"),
                Token(None, TOKEN.ACCESSOR, ".tl")
            ],
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                res = IdField.parse_strict(t)
                self.assertEqual(res.id.typ, TOKEN.IDENTIFIER)
                for f in res.fields:
                    self.assertEqual(f.typ, TOKEN.ACCESSOR)
                i += 0

    def test_prefix_op_decl_parser(self):

        # Validate parsing of the defintion of a custom prefix operator

        tests = [
            [
                # Custom prefix operator that does absolutely nothing.
                Token(None, TOKEN.PREFIX, 'prefix'),
                Token(None, TOKEN.OP_IDENTIFIER, '++'),
                Token(None, TOKEN.PAR_OPEN, '('),
                Token(None, TOKEN.IDENTIFIER, 'arg'),
                Token(None, TOKEN.PAR_CLOSE, ')'),
                Token(None, TOKEN.CURL_OPEN, '{'),
                Token(None, TOKEN.CURL_CLOSE, '}'),

                # TODO: Custom prefix operator with function body.

                # TODO: Custom prefix operator that uses a type signature

                # TODO: Custom prefix operator that is incorcet (uses :: but no actual type sig)
            ],
        ]

        i = 0;
        for t in tests:
            with self.subTest(i=i):
                res = PrefixOpDecl.parse_strict(t)
                self.assertEqual(res.kind, FunKind.PREFIX)
                self.assertIsNone(res.fixity)
                self.assertEqual(res.id.typ, TOKEN.OP_IDENTIFIER)
                self.assertEqual(len(res.params), 1)
                self.assertEqual(res.params[0].typ, TOKEN.IDENTIFIER)
                # TODO: Declarations, statements, typesignature

                i += 1

    def test_infix_op_decl_parser(self):

        # Validate parsing of the definition of custom infix operator.
        # Note: INFIX token is validated by looking at INFIX token value.

        tests = [
            [
                Token(None, TOKEN.INFIXL, "infixl"),
                Token(None, TOKEN.INT, "5"),
                Token(None, TOKEN.OP_IDENTIFIER, "%%"),
                Token(None, TOKEN.PAR_OPEN, "("),
                Token(None, TOKEN.IDENTIFIER, "a"),
                Token(None, TOKEN.OP_IDENTIFIER, ","),
                Token(None, TOKEN.IDENTIFIER, "b"),
                Token(None, TOKEN.PAR_CLOSE, ")"),
                Token(None, TOKEN.CURL_OPEN, "{"),
                Token(None, TOKEN.CURL_OPEN, "}"),

                # TODO: Custom infixl operator with function body.

                # TODO: Custom infixr operator with function body.

                # TODO: Custom infixl operator with type signature

                # TODO: Custom infixr operator with type signature
            ]
        ]

        i = 0;
        for t in tests:
            with self.subTest(i=i):
                res = PrefixOpDecl.parse_strict(t)
                if res.id.val == 'infixl':
                    self.assertEqual(res.kind.typ, TOKEN.INFIXL)
                elif res.id.val == 'infixr':
                    self.assertEqual(res.kind.typ, TOKEN.INFIXR)
                self.assertEqual(res.fixity, TOKEN.INT)
                self.assertEqual(res.id.typ, TOKEN.OP_IDENTIFIER)
                self.assertEqual(len(res.params), 2)
                self.assertEqual(res.params[0].typ, TOKEN.IDENTIFIER)
                self.assertEqual(res.params[1].typ, TOKEN.IDENTIFIER)
                # TODO: Declarations, statements, typesignature

                i += 1

    def test_var_decl_parser(self):

        # Validate parsing of variable declarations

        tests = [
            [
                Token(None, TOKEN.VAR, "Var"),
                Token(None, TOKEN.IDENTIFIER, "a"),
                Token(None, TOKEN.OP_IDENTIFIER, "="),
                Token(None, TOKEN.IDENTIFIER, "b"),
                Token(None, TOKEN.SEMICOLON, ";"),
            ]
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                res = VarDecl.parse_strict(t)
                if res.type.val == 'Var':
                    self.assertEqual(res.type.typ, TOKEN.VAR)
                else:
                    # TODO: Add type test
                    pass
                self.assertEqual(res.id.typ, TOKEN.IDENTIFIER)
                # TODO: Check the expression

                i += 1

    def test_basic_type_parser(self):

        # Validate parsing of basic data types

        tests = [
            [Token(None, TOKEN.TYPE_IDENTIFIER, "Int")],
            [Token(None, TOKEN.TYPE_IDENTIFIER, "Char")],
            [Token(None, TOKEN.TYPE_IDENTIFIER, "Bool")]
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                res = VarDecl.parse_strict(t)
                self.assertEqual(res.type_id, TOKEN.TYPE_IDENTIFIER)

                i += 1

    def test_tuple_type_parser(self):

        # Validate parsing of tuple types
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
        tests = [
            # Identifiers with accessors
            [
                Token(None, TOKEN.IDENTIFIER, "a.snd"),
                Token(None, TOKEN.OP_IDENTIFIER, "+"),
                Token(None, TOKEN.IDENTIFIER, "b.hd"),
            ],
            # Simple expressions
            [
                Token(None, TOKEN.IDENTIFIER, "first_val"),
                Token(None, TOKEN.OP_IDENTIFIER, "%%"),
                Token(None, TOKEN.IDENTIFIER, "second_val")
            ],
            # Boolean values
            [
                Token(None, TOKEN.BOOL, "False"),
            ],
            [
                Token(None, TOKEN.BOOL, "True"),
            ],
            [
                Token(None, TOKEN.EMPTY_LIST, "[]"),
            ],
            # Literals
            [
                Token(None, TOKEN.INT, "5314235241")
            ],
            [
                Token(None, TOKEN.CHAR, "c"),
            ],
            [
                Token(None, TOKEN.STRING, "a long piece of text"),
            ],
            # Nested expression
            [
                Token(None, TOKEN.IDENTIFIER, "a"),
                Token(None, TOKEN.OP_IDENTIFIER, "+"),
                Token(None, TOKEN.PAR_OPEN, "("),
                Token(None, TOKEN.INT, "5"),
                Token(None, TOKEN.PAR_OPEN, ")"),
            ],
            # Function call
            [
                Token(None, TOKEN.IDENTIFIER, "sum"),
                Token(None, TOKEN.CURL_OPEN, "("),
                Token(None, TOKEN.IDENTIFIER, "a"),
                Token(None, TOKEN.OP_IDENTIFIER, ","),
                Token(None, TOKEN.IDENTIFIER, "b"),
                Token(None, TOKEN.BRACK_CLOSE, ")"),
            ],
            # More complex nested expression
            [
                Token(None, TOKEN.PAR_OPEN, "("),
                Token(None, TOKEN.PAR_OPEN, "("),
                Token(None, TOKEN.IDENTIFIER, "a"),
                Token(None, TOKEN.OP_IDENTIFIER, "*"),
                Token(None, TOKEN.IDENTIFIER, "b"),
                Token(None, TOKEN.PAR_CLOSE, ")"),
                Token(None, TOKEN.OP_IDENTIFIER, "@"),
                Token(None, TOKEN.PAR_OPEN, "("),
                Token(None, TOKEN.IDENTIFIER, "c"),
                Token(None, TOKEN.OP_IDENTIFIER, "-"),
                Token(None, TOKEN.IDENTIFIER, "d"),
                Token(None, TOKEN.PAR_CLOSE, ")"),
                Token(None, TOKEN.PAR_CLOSE, ")"),
            ],
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                res = Exp.parse_strict(t)
                self.assertEqual(len(t), len(res.contents))
                # TODO: Come up with a better way to test here.

                i += 1

if __name__ == '__main__':
    unittest.main()
