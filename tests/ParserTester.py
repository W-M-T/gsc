#!/usr/bin/env python3

import sys
import unittest

# Makes it possible to import from the parser/lexer
sys.path.insert(0, '../')

from parser import *
from parsec import ParseError
from io import StringIO
from lexer import tokenize

class ParserTester(unittest.TestCase):

    """
    Test all of the parsing functions.
    Ideally, every test would only get a list of tokens to make sure that only the parser is tested.
    However, we also have to supply the source code for error handling.
    """

    # TODO: This is currently skipped because we need to figure out how to work with *.
    @unittest.skip
    def test_import_parser(self):

        """
        Test parsing of the import statements 'from m import x'
            where "from" is the from keyword;
            m is the module name (Identifier/TypeIdentifier);
            "import" is the import keyword;
            and x can be either *
            or a comma seperated list of OpIdentifiers, Identifiers or TypeIdentifiers
            where each of these can be aliased to another OpIdentifier, Identifier or TypeIdentifier respectively.
        """

        valid_examples = [
            StringIO('''
                from StdLib import String
            '''),
            StringIO('''
                from Math import GreatestCommonDivisor as GCD, ** as &
            '''),
            StringIO('''
                from Library import *
            '''),
            StringIO('''
                from reallybadlibraryname import t as g, f as a, t
            '''),
            # Interesting scenario where you import operator * and alias it
            StringIO('''
                from StdLib import * as +
            ''')
        ]

        incorrect_examples = [
            # This aint python bro
            StringIO('''
                import test
            '''),
            # Not allowed to import everything and then alias one Identifier
            StringIO('''
                from StdLib import *, String as str
            '''),
            # Also not allowed the other way around
            StringIO('''
                from StdLib import String as str, *
            ''')
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = ImportDecl.parse_strict(tks, t)
                self.assertEqual(type(res), AST.IMPORT)

                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, ImportDecl.parse_strict, tks, t)

                i += 1

    #
    def test_fun_decl_parser(self):

        """
        Test parsing of the import statements 'f (a) :: x -> z { vardecls stmts }' where
            f is the new function name (Identifier)
            a can be a comma seperated list of arguments (Identifiers);
            x can be a space separated list of argument types (TypeIdentifiers);
            y is a return type (TypeIdentifier);
            vardecls is a number of variable declarations (VarDecl);
            stmts is a positive number of Statements.
        """

        valid_examples = [
            StringIO('''
               sum (a, b) :: Int Int -> Int { return a + b; }
            '''),
            StringIO('''
               isElem (x, y) :: Int [Int] -> Bool { return True; }
            '''),
            StringIO('''
               append (x, y) :: Int [Int] -> Void { y.hd = x; }
            '''),
            StringIO('''
                gimme_five () :: -> Int { return 5; }
            '''),
            StringIO('''
                absnothing () { break; }
            ''')
        ]

        incorrect_examples = [
            # :: Are necessary
            StringIO('''
                gimme_five () -> Int { return 5; }
            '''),
            # No statement, not allowed.
            StringIO('''
                empty_func () { Int a = 0; }
            '''),
            StringIO('''
                mult (a, b) :: Int Int -> { Int r = 0; Int i = 0; for(;i<b;i=i+1) { r = r + a } return r } 
            ''')
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = FunDecl.parse_strict(tks, t)
                self.assertEqual(type(res), AST.FUNDECL)

                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, FunDecl.parse_strict, tks, t)

                i += 1

    def test_id_parser(self):

        """
            Test parsing of identifiers.
        """

        tests = [
            StringIO("test"),
            StringIO("a.tl.fst"),
            StringIO("a.snd.fst"),
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = IdField.parse_strict(tks, t)
                print(res)
                self.assertEqual(type(res), AST.VARREF)
                i += 1

    def test_prefix_op_decl_parser(self):

        # Test parsing of the defintion of a custom prefix operator prefix o (a) { stmts } where
        # prefix is the prefix keyword;
        # o is an Opidentifier;
        # a is an Identifier
        # stmts can be any positive number of Statements

        valid_examples = [
            StringIO('''
                 prefix % (a) { continue; }
             '''),
            # Nice long prefix,
            StringIO('''
                 prefix %%!#^$% (a) { continue; }
             '''),
        ]

        incorrect_examples = [
            # No argument
            StringIO('''
                prefix % () { continue; }
            '''),
            # No prefix body
            StringIO('''
                 prefix %%!#^$% (a) { }
             '''),
            # Invalid prefix character
            StringIO('''
                 prefix %%c (a) { }
             '''),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = PrefixOpDecl.parse_strict(tks, t)
                self.assertEqual(res.kind, FunKind.PREFIX)
                self.assertIsNone(res.fixity)
                self.assertEqual(res.id.typ, TOKEN.OP_IDENTIFIER)
                self.assertEqual(len(res.params), 1)
                self.assertEqual(res.params[0].typ, TOKEN.IDENTIFIER)

                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, PrefixOpDecl.parse_strict, tks, t)

                i += 1

    def test_infix_op_decl_parser(self):

        """
        Test parsing of the definition of custom infix operator infix f o (a, b) { stmts } where
            infix can be either the keyword infixl or infixr;
            f is the fixity, a positive number;
            o is the OpIdentifier.
            a, b are Identifiers;
            stmts can be any positive number of Statements.
        """

        valid_examples = [
            StringIO('''
                infixl 5 %% (a, b) { continue; }
            '''),
            StringIO('''
                infixr 9 &&& (a, b) { break; }
            '''),
            StringIO('''
               infixr 7 ++ (a, b) :: Int Int -> Int { return a + a + b + b; }
            '''),
            StringIO('''
                infixl 25 * (a, b) :: Int Int -> Int { return a^2 + b^2; }
            '''),
        ]

        incorrect_examples = [
            # No negative fixity allowed
            StringIO('''
               infixl -5 %% (a, b) { continue; }
            '''),
            # Typo, we dont have a infixt
            StringIO('''
                infixt 5 %% (a, b) { continue; }
            '''),
            # Fixity also cannot be an expression
            StringIO('''
               infixr 5+9 %% (a, b) { continue; }
            '''),
            # Forgot one argument
            StringIO('''
                infixr 7 %% (a) { break; }
            '''),
            # Forgot curly brace
            StringIO('''
                infixr 7 %% (a) break; }
            '''),
            # Typing symbol :: given, but no actual types argument and return types provided.
            StringIO('''
                infixr 7 %% (a, b) :: { break; }
            '''),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = InfixOpDecl.parse_strict(tks, t)
                if res.id.val == 'infixl':
                    self.assertEqual(res.kind.typ, TOKEN.INFIXL)
                elif res.id.val == 'infixr':
                    self.assertEqual(res.kind.typ, TOKEN.INFIXR)
                self.assertEqual(res.id.typ, TOKEN.OP_IDENTIFIER)
                self.assertEqual(len(res.params), 2)
                self.assertEqual(res.params[0].typ, TOKEN.IDENTIFIER)
                self.assertEqual(res.params[1].typ, TOKEN.IDENTIFIER)

                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, InfixOpDecl.parse_strict, tks, t)

                i += 1

    def test_var_decl_parser(self):

        """
        Test parsing of variable declaration X i = e where
            X can be any Type;
            i is an Identifier;
            e can be any Expression.
        """

        valid_examples = [
            StringIO('Int b = 5 + c;'),
            StringIO('String a = "testing";'),
            StringIO('Bool false = False;')
        ]

        incorrect_examples = [
            # Forgot semicolon
            StringIO('''
                Var a = b
            '''),
            # Forgot to close tuple
            StringIO('''
                (Int, T c = b.tl;
            '''),
            # No type
            StringIO('''
                c = =b.tl;
            '''),
            # Identifier cannot start with capital
            StringIO('''
                String B = "test";
            '''),
            # Empty declaration is not possible
            StringIO('''
                Char c;
            '''),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = VarDecl.parse_strict(tks, t)
                self.assertEqual(type(res), AST.VARDECL)
                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, VarDecl.parse_strict, tks, t)
                i += 1

    def test_basic_type_parser(self):

        """
        Test parsing of the basic types Int, Char, Bool.
        """

        tests = [
            StringIO('Int'),
            StringIO('Char'),
            StringIO('Bool')
        ]

        i = 0
        for t in tests:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = BasicType.parse_strict(tks, t)
                self.assertEqual(type(res), AST.BASICTYPE)

                i += 1

    def test_tuple_type_parser(self):

        """
            Test parsing of (a, b) where a, b can be any Type
        """

        valid_examples = [
            StringIO('(Int, B)'),
            StringIO('(Int, Char)'),
            StringIO('(String, Int)'),
            StringIO('(Int, [Char])'),
        ]

        incorrect_examples = [
            # Missing second argument
            StringIO('(Int, )'),
            # Second argument not a type
            StringIO('(Char, t)'),
            # Unexpected comma
            StringIO('(Int,,String)'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = TupType.parse_strict(tks, t)
                self.assertEqual(type(res), AST.TUPLETYPE)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, TupType.parse_strict, tks, t)

                i += 1

    def test_list_type_parser(self):

        """
            Test parsing of list [a] where a can be any type
        """

        valid_examples = [
            StringIO('[Int]'),
            StringIO('[(Int, Char)]'),
            StringIO('[String]'),
        ]

        incorrect_examples = [
            # Lists have to be strongly-typed
            StringIO('[var]'),
            # Missing capital for Int
            StringIO('[int]'),
            # Void lists are not a thing
            StringIO('[Void]'),
            # Cannot create an untyped list
            StringIO('[]'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = ListType.parse_strict(tks, t)
                self.assertEqual(type(res), AST.LISTTYPE)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, TupType.parse_strict, tks, t)

                i += 1

    def test_type_syn_parser(self):

        """
        Test parsing of type synonyms statement 'type T1 = T2' where
            'type' is the type keyword
            T1 is your new Type
            T2 is the Type definition
        """

        valid_examples = [
            StringIO('type Age = Int'),
            StringIO('type Name = [Char]'),
            StringIO('type Coordinate = (Int, Int)'),
            StringIO('type Person = (Name, Age)')
        ]

        incorrect_examples = [
            # New type does not start with a capital
            StringIO('type number = Int'),
            # Declared type is not a type
            StringIO('type Integer = char'),
            # Invalid new type name
            StringIO('type * = Bool'),
            # Cannot define new type is empty list.
            StringIO('type List = []'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = TypeSyn.parse_strict(tks, t)
                self.assertEqual(type(res), AST.TYPESYN)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, TypeSyn.parse_strict, tks, t)

                i += 1

    def test_stmtifelse_parser(self):

        """
        Test parsing of statement 'if (e) { stmts1 } else { stmts2 } '
            where 'if' is the if keyword;
            e is any Expression;
            'else' is the else keyword;
            stmts1 are any positive number of Statements;
            and stmts2 are any positive number of Statements.
        """

        valid_examples = [
            StringIO('if (a == 2) { print(a); } else { print("Error"); }'),
            StringIO('if (b > 2 && d < 2) { break; } else { continue; }'),
            StringIO('if (7 != y) { break; }'),
            StringIO('if (x < 5) { break; } elif(x >= 5 && x < 10) { continue; } else { break; }'),
            StringIO('if (x < 5) { break; } elif(x >= 5 && x < 10) { continue; }'),
        ]

        incorrect_examples = [
            # Missing close curly bracket
            StringIO('if (True) { break; else { break; }'),
            # Typo in else keyword
            StringIO('if (True) { +a; } els { loop(); }'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = StmtIfElse.parse_strict(tks, t)
                self.assertEqual(type(res), AST.IFELSE)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, StmtIfElse.parse_strict, tks, t)

                i += 1

    def test_stmtwhile_parser(self):

        """
        Test parsing of statement 'while (e) { stmts }' where
            'while'is the while keyword;
            e can be any Expression;
            stmts can be any positive number of statements
        """

        valid_examples = [
            StringIO('while(True) { print("For ever and ever"); }'),
            StringIO('while(a > b) { a = a - 1; b = b + 1; }'),
            StringIO('while(t) { c = t ** 2; }'),
        ]

        incorrect_examples = [
            # Missing close paranthesis
            StringIO('while(a < 100000 { ++a } '),
            # Typo in while keyword
            StringIO('whil (test) { break }'),
            # Empty while statement
            StringIO('while () { a(); }'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = StmtWhile.parse_strict(tks, t)
                self.assertEqual(type(res), AST.LOOP)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, StmtWhile.parse_strict, tks, t)

                i += 1

    def test_stmtfor_parser(self):

        """
        Test parsing of statement for (init ; cond ; upd) { stmts } where
            init can be any ActStmt;
            cond can be any Expression;
            upd can be any ActStmt;
            stmts can be any positive number of statements
        """

        valid_examples = [
            StringIO('for (i=0;i <= 10; i = i + 1) { print(i); }'),
            StringIO('for (j=0;j != 10; inc(j)) { j = j - 2; }'),
            # No initial or update, which is allowed according to the lang specs.
            StringIO('for (;k != 10;) { k = k * 2; }')
        ]

        incorrect_examples = [
            # Expressions not allowed in update
            StringIO('for (i=0;i <= 10; i = ++i) { print(i); }'),
            # Empty body is not allowed
            StringIO('for (j=0;i<3;j=j/2) { }'),
            # Missing semi colon
            StringIO('for (i=0;i <= 10 i = i + 1) { }'),
            # There is no such thing as a foreach pleb
            StringIO('foreach (i=0;i <= 10; i = ++i) { print(i); }'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = StmtFor.parse_strict(tks, t)
                self.assertEqual(type(res), AST.LOOP)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, StmtIfElse.parse_strict, tks, t)

                i += 1

        pass

    def test_stmtret_parser(self):

        """
        Test parsing of statement 'return e' where
            'return' is the return keyword;
            and e can be any Expression.
        """

        valid_examples = [
            StringIO('return x < 5;'),
            StringIO('return;'),
            StringIO('return (True);'),

        ]

        incorrect_examples = [
            # Statement after return
            StringIO('return if'),
            # No semicolon
            StringIO('return'),
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                res = StmtRet.parse_strict(tks, t)
                self.assertEqual(type(res), AST.RETURN)

                i += 1

        i = 0
        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))
                self.assertRaises(ParseError, StmtRet.parse_strict, tks, t)

                i += 1

        pass

    def test_exp_parser(self):

        """
            Test expressions, which can be of various formats.
        """

        valid_examples = [
            StringIO('''
                a.snd && b.fst
            '''),
            StringIO('''
                "Testing" == c.fst.tl
            '''),
            StringIO('''
                False
            '''),
            StringIO('''
                [] && []
            '''),
            StringIO('''
                True
            '''),
            StringIO('''
                []
            '''),
            StringIO('''
                a + (5)
            '''),
            StringIO('''
                sum(a, b)
            '''),
            StringIO('''
                (a %% c) || (d ** a)
            '''),
            StringIO('''
                a + -b
            '''),
            StringIO('''
                f(a, b, c) && g(d, e)
            '''),
            StringIO('''
                (((((((((a)))))))))
            '''),
            # Nested prefix
            StringIO('''
                a + + + b
            '''),
            # Whoever defines these prefixes aint right
            StringIO('''
                ((a + b) * c < (d ** %f) -- ^g)
            ''')
        ]

        incorrect_examples = [
            # Cannot have statements in expressions
            StringIO('''
                if (a > b) { print(a); }
            '''),
            # Bracket mismatch
            StringIO('''
                (((((((a))))
            '''),
            # Unknown constant
            StringIO('''
                Talse
            '''),
            # Accessor, not a function call
            StringIO('''
                c.snd()
            '''),
            # Float TODO: Figure out why this produces a lexer error.
            #StringIO('''
            #    52452.1515
            #''')
        ]

        i = 0
        for t in valid_examples:
            with self.subTest(i=i):
                try:
                    tks = list(tokenize(t))
                    parsed = Exp.parse_strict(tks, t)
                except Exception as e:
                    print(e)
                self.assertEqual(type(parsed), AST.DEFERREDEXPR)
                i += 1

        for t in incorrect_examples:
            with self.subTest(i=i):
                tks = list(tokenize(t))

                self.assertRaises(ParseError, Exp.parse_strict, tks, t)

                i += 1

if __name__ == '__main__':
    unittest.main()
