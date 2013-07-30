import unittest
from expression import *

class ParserTestCase(unittest.TestCase):
    def test_parse_empty(self):
        tokens = parse("")
        self.assertEqual(0, len(tokens))

    def test_parse_whitespaces(self):
        tokens = parse(" \n ")
        self.assertEqual(0, len(tokens))

        tokens = parse("100")
        self.assertEqual(1, len(tokens))

        tokens = parse("  100")
        self.assertEqual(1, len(tokens))

        tokens = parse("100  ")
        self.assertEqual(1, len(tokens))

        tokens = parse("  100  ")
        self.assertEqual(1, len(tokens))

        tokens = parse("  1 + 1  ")
        self.assertEqual(3, len(tokens))

    def assertFirstToken(self, string, expvalue, exptype, length=None):
        tokens = parse(string)
        if length != None:
            self.assertEqual(length, len(tokens))
        value, ttype = tokens[0]
        self.assertEqual(value, expvalue)
        self.assertEqual(ttype, exptype)

    def assertTokens(self, string, expvalues, exptypes, length=None):
        tokens = parse(string)
        if length != None:
            self.assertEqual(length, len(tokens))
        values = list(token[0] for token in tokens)
        types = list(token[1] for token in tokens)
        self.assertSequenceEqual(values, expvalues)
        self.assertSequenceEqual(types, exptypes)

    def test_integers(self):
        self.assertFirstToken("100", "100", TINTEGER)
        self.assertFirstToken("100 ", "100", TINTEGER)
        self.assertFirstToken(" 100 ", "100", TINTEGER)

        with self.assertRaises(SyntaxError):
            parse("10a")

    def test_operators(self):
        self.assertFirstToken("+", "+", TOPERATOR, 1)
        self.assertFirstToken("!=", "!=", TOPERATOR, 1)
        self.assertFirstToken("==", "==", TOPERATOR, 1)
        self.assertFirstToken("===", "==", TOPERATOR, 2)
        self.assertFirstToken("+*", "+", TOPERATOR, 2)

    def test_identifier(self):
        self.assertFirstToken("parsley", "parsley", TIDENTIFIER, 1)
        self.assertFirstToken("_sage_10", "_sage_10", TIDENTIFIER, 1)
        self.assertFirstToken("rozmarín", "rozmarín", TIDENTIFIER, 1)

    def test_float(self):
        self.assertFirstToken("10.", "10.", TFLOAT, 1)
        self.assertFirstToken("10.20", "10.20", TFLOAT, 1)
        self.assertFirstToken("  10.", "10.", TFLOAT, 1)

        self.assertFirstToken("10e20", "10e20", TFLOAT, 1)
        self.assertFirstToken("10.e30", "10.e30", TFLOAT, 1)
        self.assertFirstToken("10.20e30", "10.20e30", TFLOAT, 1)
        self.assertFirstToken("10.20e-30", "10.20e-30", TFLOAT, 1)
        self.assertFirstToken(" 1.2e-3 ", "1.2e-3", TFLOAT, 1)
        self.assertFirstToken(" 1.2e-3-", "1.2e-3", TFLOAT, 2)
        self.assertFirstToken(" 1.2-", "1.2", TFLOAT, 2)

        with self.assertRaises(SyntaxError):
            parse("10.a")

        with self.assertRaises(SyntaxError):
            parse("10ea")

        with self.assertRaises(SyntaxError):
            parse("10e*")

    def test_single(self):
        self.assertFirstToken("(", "(", TLPAR, 1)
        self.assertFirstToken("(1", "(", TLPAR, 2)
        self.assertFirstToken("((", "(", TLPAR, 2)
        self.assertFirstToken(")", ")", TRPAR, 1)
        self.assertFirstToken(")1", ")", TRPAR, 2)
        self.assertFirstToken(")(", ")", TRPAR, 2)

        self.assertFirstToken("[", "[", TLBRACKET)
        self.assertFirstToken("[]", "[", TLBRACKET, 2)
        self.assertFirstToken("]", "]", TRBRACKET)
        self.assertFirstToken(",", ",", TCOMMA)
        self.assertFirstToken(";", ";", TSEMICOLON)
        self.assertFirstToken(":", ":", TCOLON)

    def test_mix(self):
        self.assertTokens("100+", ["100", "+"], [TINTEGER, TOPERATOR], 2)
        self.assertTokens("+sage", ["+", "sage"], [TOPERATOR, TIDENTIFIER], 2)
        self.assertTokens("sage+", ["sage", "+"], [TIDENTIFIER, TOPERATOR], 2)
        self.assertTokens("10 - parsley+sage2 != _rosemary",
                          ["10", "-", "parsley", "+", "sage2", "!=", "_rosemary"],
                          [TINTEGER, TOPERATOR, TIDENTIFIER, TOPERATOR,
                              TIDENTIFIER, TOPERATOR, TIDENTIFIER], 7)

    def test_string(self):
        self.assertFirstToken("'thyme'", "thyme", TSTRING)
        self.assertFirstToken('"thyme"', "thyme", TSTRING)

        self.assertFirstToken("'parsley rosemary'", "parsley rosemary", TSTRING)
        self.assertFirstToken('"parsley rosemary"', "parsley rosemary", TSTRING)

        self.assertFirstToken('"quote \\""', 'quote \\"', TSTRING)
        with self.assertRaises(SyntaxError):
            parse("'not good")

        with self.assertRaises(SyntaxError):
            parse("'not good\"")
