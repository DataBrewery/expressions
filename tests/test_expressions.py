# -*- encoding: utf8 -*-
import unittest
from expressions import *


class StringReaderTestCase(unittest.TestCase):
    def test_tokenize_empty(self):
        tokens = tokenize(u"")
        self.assertEqual(0, len(tokens))

    def test_tokenize_whitespaces(self):
        tokens = tokenize(u" \n ")
        self.assertEqual(0, len(tokens))

        tokens = tokenize(u"100")
        self.assertEqual(1, len(tokens))

        tokens = tokenize(u"  100")
        self.assertEqual(1, len(tokens))

        tokens = tokenize(u"100  ")
        self.assertEqual(1, len(tokens))

        tokens = tokenize(u"  100  ")
        self.assertEqual(1, len(tokens))

        tokens = tokenize(u"  1 + 1  ")
        self.assertEqual(3, len(tokens))

    def assertFirstToken(self, string, expvalue, exptype, length=None):
        tokens = tokenize(string)
        if length is not None:
            self.assertEqual(length, len(tokens))
        value = tokens[0].value
        ttype = tokens[0].type
        self.assertEqual(value, expvalue)
        self.assertEqual(ttype, exptype)

    def assertTokens(self, string, expvalues, exptypes, length=None):
        tokens = tokenize(string)
        if length is not None:
            self.assertEqual(length, len(tokens))
        values = list(token.value for token in tokens)
        types = list(token.type for token in tokens)
        self.assertSequenceEqual(values, expvalues)
        self.assertSequenceEqual(types, exptypes)

    def test_integers(self):
        self.assertFirstToken(u"100", 100, INTEGER)
        self.assertFirstToken(u"100 ", 100, INTEGER)
        self.assertFirstToken(u" 100 ", 100, INTEGER)

        with self.assertRaises(SyntaxError):
            tokenize(u"10a")

    def test_operators(self):
        self.assertFirstToken(u"+", u"+", OPERATOR, 1)
        self.assertFirstToken(u"!=", u"!=", OPERATOR, 1)
        self.assertFirstToken(u"==", u"==", OPERATOR, 1)
        self.assertFirstToken(u"===", u"==", OPERATOR, 2)
        self.assertFirstToken(u"+*", u"+", OPERATOR, 2)

    def test_keyword_operators(self):
        class case_insensitive_dialect(default_dialect):
            case_sensitive = False

        class case_sensitive_dialect(default_dialect):
            case_sensitive = True

        register_dialect("case_insensitive", case_insensitive_dialect)
        register_dialect("case_sensitive", case_sensitive_dialect)

        tokens = tokenize(u"parsley or rosemary and thyme", "case_sensitive")
        types = [t.type for t in tokens]
        self.assertSequenceEqual([IDENTIFIER, OPERATOR, IDENTIFIER, OPERATOR,
                                    IDENTIFIER], types)

        tokens = tokenize(u"AND and OR or", "case_sensitive")
        types = [t.type for t in tokens]
        self.assertSequenceEqual([IDENTIFIER, OPERATOR, IDENTIFIER, OPERATOR],
                                 types)

        tokens = tokenize(u"AND and OR or", "case_insensitive")
        types = [t.type for t in tokens]
        self.assertSequenceEqual([OPERATOR, OPERATOR, OPERATOR, OPERATOR],
                                 types)

    def test_identifier(self):
        self.assertFirstToken(u"parsley", u"parsley", IDENTIFIER, 1)
        self.assertFirstToken(u"_sage_10", u"_sage_10", IDENTIFIER, 1)
        self.assertFirstToken(u"rozmarín", u"rozmarín", IDENTIFIER, 1)

    def test_float(self):
        self.assertFirstToken(u"10.", 10., FLOAT, 1)
        self.assertFirstToken(u"10.20", 10.20, FLOAT, 1)
        self.assertFirstToken(u"  10.", 10., FLOAT, 1)

        self.assertFirstToken(u"10e20", 10e20, FLOAT, 1)
        self.assertFirstToken(u"10.e30", 10.e30, FLOAT, 1)
        self.assertFirstToken(u"10.20e30", 10.20e30, FLOAT, 1)
        self.assertFirstToken(u"10.20e-30", 10.20e-30, FLOAT, 1)
        self.assertFirstToken(u" 1.2e-3 ", 1.2e-3, FLOAT, 1)
        self.assertFirstToken(u" 1.2e-3-", 1.2e-3, FLOAT, 2)
        self.assertFirstToken(u" 1.2-", 1.2, FLOAT, 2)

        with self.assertRaises(SyntaxError):
            tokenize(u"10.a")

        with self.assertRaises(SyntaxError):
            tokenize(u"10ea")

        with self.assertRaises(SyntaxError):
            tokenize(u"10e*")

    def test_single(self):
        self.assertFirstToken(u"(", u"(", LPAREN, 1)
        self.assertFirstToken(u"(1", u"(", LPAREN, 2)
        self.assertFirstToken(u"((", u"(", LPAREN, 2)
        self.assertFirstToken(u")", u")", RPAREN, 1)
        self.assertFirstToken(u")1", u")", RPAREN, 2)
        self.assertFirstToken(u")(", u")", RPAREN, 2)

        self.assertFirstToken(u"[", u"[", LBRACKET)
        self.assertFirstToken(u"[]", u"[", LBRACKET, 2)
        self.assertFirstToken(u"]", u"]", RBRACKET)
        self.assertFirstToken(u",", u",", COMMA)
        self.assertFirstToken(u";", u";", SEMICOLON)
        self.assertFirstToken(u":", u":", COLON)

    def test_mix(self):
        self.assertTokens(u"100+", [100, u"+"], [INTEGER, OPERATOR], 2)
        self.assertTokens(u"+sage", [u"+", u"sage"], [OPERATOR, IDENTIFIER], 2)
        self.assertTokens(u"sage+", [u"sage", u"+"], [IDENTIFIER, OPERATOR], 2)
        self.assertTokens(u"10 - parsley+sage2 != _rosemary",
                          [10, u"-", u"parsley", u"+", u"sage2", u"!=", u"_rosemary"],
                          [INTEGER, OPERATOR, IDENTIFIER, OPERATOR,
                              IDENTIFIER, OPERATOR, IDENTIFIER], 7)

    def test_string(self):
        self.assertFirstToken(u"'thyme'", u"thyme", STRING)
        self.assertFirstToken(u'"thyme"', u"thyme", STRING)

        self.assertFirstToken(u"'parsley rosemary'", u"parsley rosemary", STRING)
        self.assertFirstToken(u'"parsley rosemary"', u"parsley rosemary", STRING)

        self.assertFirstToken(u'"quote \\""', u'quote \\"', STRING)
        with self.assertRaises(SyntaxError):
            tokenize(u"'not good")

        with self.assertRaises(SyntaxError):
            tokenize(u"'not good\"")

class ParserTestCase(unittest.TestCase):
    def assertTokens(self, string, expvalues, exptypes, length=None):
        tokens = parse(string)

        if length is not None:
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

    def test_unary(self):
        self.assertTokens("-x",
                          ["x", "-"],
                          [VARIABLE, OPERATOR])

        self.assertTokens("- - x",
                          ["x", "-", "-"],
                          [VARIABLE, OPERATOR, OPERATOR])

        self.assertTokens("x - y",
                          ["x", "y", "-"],
                          [VARIABLE, VARIABLE, OPERATOR])

        self.assertTokens("x + - y",
                          ["x", "y", "-", "+"],
                          [VARIABLE, VARIABLE, OPERATOR, OPERATOR])

        self.assertTokens("- x + y",
                          ["x", "-", "y", "+"],
                          [VARIABLE, OPERATOR, VARIABLE, OPERATOR])

    def test_unary_keword(self):
        self.assertTokens("not A",
                          ["A", "not"],
                          [VARIABLE, OPERATOR])

        self.assertTokens("A and not B",
                          ["A", "B", "not", "and"],
                          [VARIABLE, VARIABLE, OPERATOR, OPERATOR])


class ValidatingCompiler(Compiler):
    def compile_variable(self, context, variable):
        if variable not in context:
            raise ExpressionError(variable)
    def compile_function(self, context, function, args):
        if function not in context:
            raise ExpressionError(function)
    def compile_literal(self, context, literal):
        pass
    def compile_operator(self, context, operator, op1, op2):
        pass

class FunctionCompiler(Compiler):
    def compile_variable(self, context, variable):
        return variable
    def compile_function(self, context, function, args):
        return "CALL %s(%s)" % (function, ", ".join(args))

class CompilerTestCase(unittest.TestCase):
    def test_validating_compiler(self):
        compiler = ValidatingCompiler()
        result = compiler.compile("a+a", ["a", "b"])

    def test_function_call_compile(self):
        compiler = FunctionCompiler()

        result = compiler.compile("f()")
        self.assertEqual("CALL f()", result)

        result = compiler.compile("f(x)")
        self.assertEqual("CALL f(x)", result)

        result = compiler.compile("f(x, y)")
        self.assertEqual("CALL f(x, y)", result)
