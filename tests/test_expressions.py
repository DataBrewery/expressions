import unittest
from expressions import *


class StringReaderTestCase(unittest.TestCase):
    def test_tokenize_empty(self):
        tokens = tokenize("")
        self.assertEqual(0, len(tokens))

    def test_tokenize_whitespaces(self):
        tokens = tokenize(" \n ")
        self.assertEqual(0, len(tokens))

        tokens = tokenize("100")
        self.assertEqual(1, len(tokens))

        tokens = tokenize("  100")
        self.assertEqual(1, len(tokens))

        tokens = tokenize("100  ")
        self.assertEqual(1, len(tokens))

        tokens = tokenize("  100  ")
        self.assertEqual(1, len(tokens))

        tokens = tokenize("  1 + 1  ")
        self.assertEqual(3, len(tokens))

    def assertFirstToken(self, string, expvalue, exptype, length=None):
        tokens = tokenize(string)
        if length != None:
            self.assertEqual(length, len(tokens))
        value = tokens[0].value
        ttype = tokens[0].type
        self.assertEqual(value, expvalue)
        self.assertEqual(ttype, exptype)

    def assertTokens(self, string, expvalues, exptypes, length=None):
        tokens = tokenize(string)
        if length != None:
            self.assertEqual(length, len(tokens))
        values = list(token.value for token in tokens)
        types = list(token.type for token in tokens)
        self.assertSequenceEqual(values, expvalues)
        self.assertSequenceEqual(types, exptypes)

    def test_integers(self):
        self.assertFirstToken("100", 100, INTEGER)
        self.assertFirstToken("100 ", 100, INTEGER)
        self.assertFirstToken(" 100 ", 100, INTEGER)

        with self.assertRaises(SyntaxError):
            tokenize("10a")

    def test_operators(self):
        self.assertFirstToken("+", "+", OPERATOR, 1)
        self.assertFirstToken("!=", "!=", OPERATOR, 1)
        self.assertFirstToken("==", "==", OPERATOR, 1)
        self.assertFirstToken("===", "==", OPERATOR, 2)
        self.assertFirstToken("+*", "+", OPERATOR, 2)

    def test_identifier(self):
        self.assertFirstToken("parsley", "parsley", IDENTIFIER, 1)
        self.assertFirstToken("_sage_10", "_sage_10", IDENTIFIER, 1)
        self.assertFirstToken("rozmarín", "rozmarín", IDENTIFIER, 1)

    def test_float(self):
        self.assertFirstToken("10.", 10., FLOAT, 1)
        self.assertFirstToken("10.20", 10.20, FLOAT, 1)
        self.assertFirstToken("  10.", 10., FLOAT, 1)

        self.assertFirstToken("10e20", 10e20, FLOAT, 1)
        self.assertFirstToken("10.e30", 10.e30, FLOAT, 1)
        self.assertFirstToken("10.20e30", 10.20e30, FLOAT, 1)
        self.assertFirstToken("10.20e-30", 10.20e-30, FLOAT, 1)
        self.assertFirstToken(" 1.2e-3 ", 1.2e-3, FLOAT, 1)
        self.assertFirstToken(" 1.2e-3-", 1.2e-3, FLOAT, 2)
        self.assertFirstToken(" 1.2-", 1.2, FLOAT, 2)

        with self.assertRaises(SyntaxError):
            tokenize("10.a")

        with self.assertRaises(SyntaxError):
            tokenize("10ea")

        with self.assertRaises(SyntaxError):
            tokenize("10e*")

    def test_single(self):
        self.assertFirstToken("(", "(", LPAREN, 1)
        self.assertFirstToken("(1", "(", LPAREN, 2)
        self.assertFirstToken("((", "(", LPAREN, 2)
        self.assertFirstToken(")", ")", RPAREN, 1)
        self.assertFirstToken(")1", ")", RPAREN, 2)
        self.assertFirstToken(")(", ")", RPAREN, 2)

        self.assertFirstToken("[", "[", LBRACKET)
        self.assertFirstToken("[]", "[", LBRACKET, 2)
        self.assertFirstToken("]", "]", RBRACKET)
        self.assertFirstToken(",", ",", COMMA)
        self.assertFirstToken(";", ";", SEMICOLON)
        self.assertFirstToken(":", ":", COLON)

    def test_mix(self):
        self.assertTokens("100+", [100, "+"], [INTEGER, OPERATOR], 2)
        self.assertTokens("+sage", ["+", "sage"], [OPERATOR, IDENTIFIER], 2)
        self.assertTokens("sage+", ["sage", "+"], [IDENTIFIER, OPERATOR], 2)
        self.assertTokens("10 - parsley+sage2 != _rosemary",
                          [10, "-", "parsley", "+", "sage2", "!=", "_rosemary"],
                          [INTEGER, OPERATOR, IDENTIFIER, OPERATOR,
                              IDENTIFIER, OPERATOR, IDENTIFIER], 7)

    def test_string(self):
        self.assertFirstToken("'thyme'", "thyme", STRING)
        self.assertFirstToken('"thyme"', "thyme", STRING)

        self.assertFirstToken("'parsley rosemary'", "parsley rosemary", STRING)
        self.assertFirstToken('"parsley rosemary"', "parsley rosemary", STRING)

        self.assertFirstToken('"quote \\""', 'quote \\"', STRING)
        with self.assertRaises(SyntaxError):
            tokenize("'not good")

        with self.assertRaises(SyntaxError):
            tokenize("'not good\"")

class ParserTestCase(unittest.TestCase):
    def assertTokens(self, string, expvalues, exptypes, length=None):
        tokens = parse(string)

        if length != None:
            self.assertEqual(length, len(tokens))

        values = list(token.value for token in tokens)
        types = list(token.type for token in tokens)

        self.assertSequenceEqual(values, expvalues)
        self.assertSequenceEqual(types, exptypes)

    def test_basic(self):
        output = parse("1")
        self.assertEqual(1, len(output))

        output = parse("1 + 1")
        self.assertEqual(3, len(output))

        self.assertTokens("1+1", [1, 1, "+"], [LITERAL, LITERAL, OPERATOR])

    def test_precedence(self):

        self.assertTokens("1+2+3",
                          [1, 2, "+", 3, "+"],
                          [LITERAL, LITERAL, OPERATOR, LITERAL, OPERATOR])

        self.assertTokens("1*2+3",
                          [1, 2, "*", 3, "+"],
                          [LITERAL, LITERAL, OPERATOR, LITERAL, OPERATOR])

        self.assertTokens("1+2*3",
                          [1, 2, 3, "*", "+"],
                          [LITERAL, LITERAL, LITERAL, OPERATOR, OPERATOR])

    def test_parens(self):

        self.assertTokens("(1)",
                            [1],
                            [LITERAL])

        self.assertTokens("(1+1)",
                            [1, 1, "+"],
                            [LITERAL, LITERAL, OPERATOR])

        self.assertTokens("(1+2)*3",
                          [1, 2, "+", 3, "*"],
                          [LITERAL, LITERAL, OPERATOR, LITERAL, OPERATOR])

    def test_function_call(self):

        self.assertTokens("f(1)",
                          [1, "f"],
                          [LITERAL, FUNCTION])

        self.assertTokens("f(1, 2, 3)",
                          [1, 2, 3, "f"],
                          [LITERAL, LITERAL, LITERAL, FUNCTION])

        self.assertTokens("f(1+2, 3)",
                          [1, 2, "+", 3, "f"],
                          [LITERAL, LITERAL, OPERATOR, LITERAL, FUNCTION])

    def test_empty_function(self):
        tokens = parse("f()")
        token = tokens[0]
        self.assertEqual(FUNCTION, token.type)
        self.assertEqual("f", token.value)
        self.assertEqual(0, token.argc)

    def test_function_argc(self):
        tokens = parse("f(1)")
        token = tokens[1]
        self.assertEqual(FUNCTION, token.type)
        self.assertEqual(1, token.argc)

        tokens = parse("f(1, 2, 3)")
        token = tokens[3]
        self.assertEqual(FUNCTION, token.type)
        self.assertEqual(3, token.argc)

        tokens = parse("f(g(10, 12))")
        token = tokens[3]
        self.assertEqual(FUNCTION, token.type)
        self.assertEqual("f", token.value)
        self.assertEqual(1, token.argc)

        token = tokens[2]
        self.assertEqual(FUNCTION, token.type)
        self.assertEqual("g", token.value)
        self.assertEqual(2, token.argc)

    def test_identifier_and_fun(self):

        self.assertTokens("f(g)",
                          ["g", "f"],
                          [VARIABLE, FUNCTION])

class CompilerTestCase(unittest.TestCase):
    def test_foo(self):
        pass
