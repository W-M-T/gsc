#!/usr/bin/env python3

import unittest
import string
import sys

sys.path.insert(0, '../')

from lexer import REG_ID, REG_OP, REG_INT, REG_STR, REG_CHR

class RegexTester(unittest.TestCase):

    """
    Test the regexes that are used to match the tokens.
    """

    disallowed = ['\0','\a','\b','\f','\n','\r','\t','\v','\\','\"','\'']
    allowed = ['\\0', '\\a', '\\b', '\\f', '\\n', '\\r', '\\t', '\\v', '\\\\', '\\\'', '\\\"']

    def compare(self, regex, value, msg):
        r = regex.match(value)
        self.assertIsNotNone(r, msg % value)
        if r is not None:
            self.assertEqual(value, r.group(0))

    def test_character_regex(self):
        """
        Test regex that is used to match chars
        """

        for c in self.allowed + list(filter(lambda x: x not in self.disallowed, string.printable)):
            with self.subTest():
                self.compare(REG_CHR, "'" + str(c) + "'", "Character %s was not matched")

    def test_identifier_regex(self):
        """
        Test regex that is used to match identifiers
        """
        for f in string.ascii_lowercase:
            for d in string.ascii_letters + '_':
                with self.subTest():
                    self.compare(REG_ID, f + d, "Identifier %s was not matched")

    def test_operator_regex(self):
        """
        Test regex that is used to match operators

        """
        op_chars = ['!','#','$','%','&','*','+','/','<','=','>','?','@','\\','^','|','-','~',',',':']
        for k in range(1, 4):
            for op in op_chars:
                operator = op * k
                with self.subTest():
                    self.compare(REG_OP, operator, "Operator %s was not matched")

    def test_integer_regex(self):
        """
        Test regex that is used to match integers
        
        We choose a range between -11 and 11 since this way we can match
        negative numbers, 0 and positive numbers and numbers consisting
        of multiple digits.
        """
        for i in range(0, 1000):
            with self.subTest():
                self.compare(REG_INT, str(i), "Integer %s was not matched")

    def test_string_regex(self):
        """
        Test regex that is used to match strings
        """
        strings = [
            "Dit is een test string\n met meerdere regels"
            "\t ik hou van tabs \t en verticale \v tabs"
            "Geen idee wat deze characters doen \a\b0asgd34"
            "Ik ram op mijn toegwgetr530524315254235\agre442hrw5034952-9554yjgi(*&^%$#@!"
            "\\"
            "",
            "\\f\r\'"
            ]

        for s in strings:
            for k in range(0, len(s)):
                # Check if current single letter character is allowed 
                if s[k] not in list(filter(lambda x: x not in self.disallowed, string.printable)) or s[k] == '\\':
                    if s[k] == '\\':
                        # Check if current character is an escape sequence
                        self.assertIn(s [k:k+1], allowed, "Character %s is not a valid escape sequence", s[k:k+1])
                    else:               
                        self.assertEqual(s[k], '\\', "Character %s is not allowed and is not an escape character" % s[k])


if __name__ == '__main__':
    unittest.main()
