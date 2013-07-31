# -*- encoding: utf8 -*-

import unicodedata
from collections import namedtuple

class ExpressionError(Exception):
    """Raised by the expression compiler"""
    pass

__all__ = (
            "tokenize",
            "Expression",
            "ExpressionError",

            "INTEGER",
            "FLOAT",
            "STRING",
            "IDENTIFIER",

            "LITERAL",
            "VARIABLE",
            "FUNCTION",

            "OPERATOR",
            "LPAREN",
            "RPAREN",
            "LBRACKET",
            "RBRACKET",
            "COMMA",
            "COLON",
            "SEMICOLON",
        )

# Tokens:

INTEGER = 'int'           # 10
FLOAT = 'float'           # 10.1
STRING = 'str'            # "abc" or 'abc'
OPERATOR = 'op'           # + - * /
IDENTIFIER = 'ident'
LITERALS = (INTEGER, FLOAT, STRING)

LITERAL = 'const'
VARIABLE = 'var'
FUNCTION = 'func'

LPAREN = '('
RPAREN = ')'
LBRACKET = '['
RBRACKET = ']'
COMMA = ','
COLON = ':'
SEMICOLON = ';'

# Unicode categories
# Source: http://www.unicode.org/Public/5.1.0/ucd/UCD.html#General_Category_Values

CAT_SEPARATOR = 'Z'
CAT_CONTROL = 'C'
CAT_NUMBER = 'N'
CAT_LETTER = 'L'
CAT_IDENTIFIER = CAT_NUMBER + CAT_LETTER
CAT_SYMBOL = 'S'
SUBCAT_MATH = 'm'

OPERATOR_CHARS = '+-*/!=<>%?|~'
IDENTIFIER_START_CHARS = '_' # TODO: add @
COMPOSED_OPERATORS = ( "!=", "==", "<=", ">=", "&&", "||", "**" )
STRING_ESCAPE_CHAR = '\\'

class _StringReader(object):
    def __init__(self, string):
        self.string = string
        self.length = len(string)
        self.pos = 0
        self.char = None
        self.category = None
        self.subcategory = None

        # Advance to the first character
        if string:
            self.char = self.string[0]
            (self.category, self.subcategory) = unicodedata.category(self.char)

    def next(self):
        """Proceeds to the next character. Returns a tuple (`char`,
        `category`). Raises `IndexError` when at the end."""

        if self.at_end():
            self.pos = self.length
            return (None, None)

        self.pos += 1

        self.char = self.string[self.pos]
        (self.category, self.subcategory) = unicodedata.category(self.char)

        return (self.char, self.category)

    def at_end(self):
        return self.pos + 1 >= self.length

    def peek(self):
        """Return next character or empty string if at end."""
        if not self.at_end():
            return self.string[self.pos+1]
        else:
            return None

    def peek_category(self):
        """Return category of the next character"""
        if not self.at_end():
            return unicodedata.category(self.string[self.pos+1])[0]
        else:
            return None

    def __bool__(self):
        return self.pos < self.length

    def skip_whitespace(self):
        """Moves the reader to the first non-whitespace character."""
        while(self and (self.category == CAT_SEPARATOR \
                            or self.category == CAT_CONTROL)):
            self.next()

    def __repr__(self):
        return "{pos=%s, c=%s, cat=%s%s}" % (self.pos, repr(self.char),
                                     self.category, self.subcategory)

    def consume(self, category=None, characters=None):
        """Consumes characters of category `category` or from a list of
        `characters`. Stops at last occurence of such character."""

        if category and characters:
            while(self and (self.category in category
                                or self.char in characters)):
                self.next()
        elif category:
            while(self and self.category in category):
                self.next()
        elif characters:
            while(self and self.char in characters):
                self.next()

        self.pos -= 1

    def consume_numeric(self):
        """Consumes a numeric value and returns the consumed token type"""
        token_type = INTEGER
        self.consume(category=CAT_NUMBER)

        if self.peek() == ".":
            token_type = FLOAT
            self.next()

            if self.peek_category() == CAT_NUMBER:
                self.next()
                self.consume(category=CAT_NUMBER)


        if self.at_end():
            return token_type

        if self.peek() in "eE":
            token_type = FLOAT
            self.next()
            if self.peek() in "+-":
                self.next()
            elif self.peek_category() != CAT_NUMBER:
                raise SyntaxError("Number expected after exponent")
            # Advance to the first number to consume it
            self.next()
            self.consume(category=CAT_NUMBER)

        elif self.peek_category() == CAT_LETTER:
            raise SyntaxError("Letter in a number")

        return token_type

    def consume_string(self, quote):
        escape = False

        while(self):
            self.next()
            if self.char == quote and not escape:
                break

            if not escape and self.char == STRING_ESCAPE_CHAR:
                escape = True
            else:
                escape = False

        if not self and self.char != quote:
            raise SyntaxError("Missing string end quote")

    def tokenize(self):
        """Parse the string and return tokens. This is one-time method."""

        tokens = []
        while(True):
            self.skip_whitespace()
            if not self:
                break

            token_type = None
            start = self.pos

            # Integer
            if self.category == CAT_NUMBER:
                token_type = self.consume_numeric()

            # Identifier
            elif self.category == CAT_LETTER \
                    or self.char in IDENTIFIER_START_CHARS:

                token_type = IDENTIFIER

                if self.char in IDENTIFIER_START_CHARS:
                    self.next()
                self.consume(CAT_IDENTIFIER, IDENTIFIER_START_CHARS)

            # Operator
            elif self.char in OPERATOR_CHARS:
                token_type = OPERATOR
                peek = self.peek()
                if peek:
                    composed = self.char + peek
                    if composed in COMPOSED_OPERATORS:
                        self.next()

            elif self.char == "'" or self.char == '"':
                token_type = STRING
                self.consume_string(self.char)
            elif self.char == '(':
                token_type = LPAREN
            elif self.char == ')':
                token_type = RPAREN
            elif self.char == '[':
                token_type = LBRACKET
            elif self.char == ']':
                token_type = RBRACKET
            elif self.char == ',':
                token_type = COMMA
            elif self.char == ':':
                token_type = COLON
            elif self.char == ';':
                token_type = SEMICOLON
            else:
                raise SyntaxError("Unknown character %s, category %s%s" %
                                            (repr(self.char),
                                             self.category,
                                             self.subcategory))

            token = self.string[start:self.pos+1]

            # TODO: treat escaped characters
            if token_type == STRING:
                token = token[1:-1]
            elif token_type == INTEGER:
                token = int(token)
            elif token_type == FLOAT:
                token = float(token)

            tokens.append(Token(token_type, token))

            if not self:
                break

            self.next()

        return tokens


def tokenize(string):
    """Parses the string and returns list of tokens."""
    tokens = []

    reader = _StringReader(string)

    try:
        tokens = reader.tokenize()
    except SyntaxError as e:
        raise SyntaxError("Syntax error at %s: %s" % (reader.pos, str(e)))

    return tokens


UNARY = 1
BINARY = 2

RIGHT = 1
LEFT = 2

Token = namedtuple('Token', ["type", "value"])
Element = namedtuple('Element', ["type", "value", "argc"])
Operator = namedtuple("Operator", ["name", "precedence", "assoc", "type"])

optable = (
    Operator("**", 1000, RIGHT, BINARY),
    Operator("^",  1000, RIGHT, BINARY),
    Operator("*",   900, LEFT, BINARY),
    Operator("/",   900, LEFT, BINARY),
    Operator("%",   900, LEFT, BINARY),

    Operator("+",   500, LEFT, BINARY),
    Operator("-",   500, LEFT, UNARY | BINARY),

    Operator("&",   300, LEFT, BINARY),
    Operator("^",   300, LEFT, BINARY),
    Operator("|",   300, LEFT, BINARY),

    Operator("<",   200, LEFT, BINARY),
    Operator("<=",  200, LEFT, BINARY),
    Operator(">",   200, LEFT, BINARY),
    Operator(">=",  200, LEFT, BINARY),
    Operator("!=",  200, LEFT, BINARY),
    Operator("==",  200, LEFT, BINARY),
    Operator("in",  200, LEFT, BINARY),
    Operator("is",  200, LEFT, BINARY),
    Operator("not in", 200, LEFT, BINARY),
    Operator("is not", 200, LEFT, BINARY),

    Operator("not", 120, LEFT, UNARY),

    Operator("and", 110, LEFT, BINARY),
    Operator("or",  100, LEFT, BINARY),
)

class Expression(object):

    def __init__(self, string):
        self.string = string
        self.operators = {}
        self.precedence = {}

        for op in optable:
            self.operators[op.name] = op
            self.precedence[op.name] = op.precedence

        self.stack = []
        self.output = []

        self.tokens = tokenize(string)
        self._parse()

    def _parse(self):
        """Parse `string`. `operators` is a dictionary of named operators where
        values is their priority."""

        # Shunting-yard algorithm
        # Variable function arguments:
        # http://www.kallisti.net.nz/blog/2008/02/extension-to-the-shunting-yard-algorithm-to-allow-variable-numbers-of-arguments-to-functions/

        self.stack = []
        self.output = []
        self.were_values = []
        self.argc = []

        for i, token in enumerate(self.tokens):
            # The next_token is used only to identify whether identifier is a
            # variable name or a function call

            if i + 1 < len(self.tokens):
                next_token = self.tokens[i+1]
                if token.type == IDENTIFIER and next_token.type == LPAREN:
                    token = Token(FUNCTION, token.value)

            self._parse_token(token)

        # ... When there are no more tokens to read:
        # While there are still operator tokens in the stack:
        while(self.stack):
            token = self.stack.pop()

            # If the operator token on the top of the stack is a parenthesis,
            # then there are mismatched parentheses.
            if token.type == RPAREN:
                raise SyntaxError("Missing right parethesis")

            # Pop the operator onto the output queue.
            self.output.append(token)

    def _parse_token(self, token):

        # Shunting-yard algorithm:
        #         http://en.wikipedia.org/wiki/Shunting-yard_algorithm

        # If the token is a number, then add it to the output queue.
        if token.type in LITERALS:
            self.output.append(Element(LITERAL, token.value, 0))

            if self.were_values:
                self.were_values[-1] = True

        # ... same situation as above
        elif token.type == IDENTIFIER:
            self.output.append(Element(VARIABLE, token.value, 0))

            if self.were_values:
                self.were_values[-1] = True

        # If the token is a function token, then push it onto the stack.
        elif token.type == FUNCTION:
            self.stack.append(Element(FUNCTION, token.value, 0))
            self.argc.append(0)

            if self.were_values:
                self.were_values[-1] = True
            self.were_values.append(False)

        # If the token is a function argument separator (e.g., a comma):
        elif token.type == COMMA:
            # Until the token at the top of the stack is a left parenthesis,
            # pop operators off the stack onto the output queue. If no left
            # parentheses are encountered, either the separator was misplaced
            # or parentheses were mismatched.
            while(self.stack):
                if self.stack[-1].type == LPAREN:
                    break
                self.output.append(self.stack.pop())

            if self.were_values.pop():
                # Increase argument count
                self.argc.append(self.argc.pop() + 1)
            self.were_values.append(False)

        # If the token is an operator, o1, then:
        elif token.type == OPERATOR:
            op1 = self.operators[token.value]

            if op1.type == UNARY:
                self.stack.push(Element(OPERATOR, token.value, 1))

            else:
                # while there is an operator token, o2, at the top of the
                # stack, and either o1 is left-associative and its precedence
                # is equal to that of o2, or o1 has precedence less than that
                # of o2, pop o2 off the stack, onto the output queue;

                while(self.stack):
                    token2 = self.stack[-1]
                    if token2.type != OPERATOR:
                        break
                    op2 = self.operators[token2.value]

                    p1 = self.precedence[op1.name]
                    p2 = self.precedence[op2.name]

                    is_lassoc = op1.assoc == LEFT
                    if not ((is_lassoc and p1 == p2) or p1 < p2):
                        break

                    # push o1 onto the stack.
                    self.output.append(self.stack.pop())

                self.stack.append(Element(OPERATOR, token.value, 2))

        # If the token is a left parenthesis, then push it onto the stack.
        elif token.type == LPAREN:
            self.stack.append(Element(LPAREN, '(', 0))

        # If the token is a right parenthesis:
        elif token.type == RPAREN:
            # Until the token at the top of the stack is a left parenthesis,
            # pop operators off the stack onto the output queue.
            while(self.stack):
                if self.stack[-1].type == LPAREN:
                    break
                self.output.append(self.stack.pop())

            # Pop the left parenthesis from the stack, but not onto the
            # output queue.
            self.stack.pop()

            # If the token at the top of the stack is a function token, pop it
            # onto the output queue.
            if self.stack and self.stack[-1].type == FUNCTION:
                func = self.stack.pop()
                argc = self.argc.pop()
                if self.were_values.pop():
                    argc += 1

                self.output.append(Element(FUNCTION, func.value, argc))

            # If the stack runs out without finding a left parenthesis, then
            # there are mismatched parentheses.

    def compile(self, compiler):
        """Compile the expression using `compiler`. The `compiler` should
        implement:

        * `compile_literal(literal)` – integer, float or string literal
        * `compile_variable(variable)` – variable name
        * `compile_operator(operator, op1, op2)` – binary operator
        * `compile_function(function, args)` – function call with arguments
        """

        stack = []
        for token in self.output:
            if token.type == LITERAL:
                value = compiler.compile_literal(token.value)

            elif token.type == VARIABLE:
                value = compiler.compile_variable(token.value)

            elif token.type == OPERATOR:
                op2 = stack.pop()
                op1 = stack.pop()

                value = compiler.compile_operator(token.value, op1, op2)

            elif token.type == FUNCTION:
                if token.argc:
                    args = stack[-token.argc:]
                else:
                    args = []

                value = complier.compile_function(token.value, args)

            else:
                raise RuntimeError("Unknown token type %s" % repr(token.type))

            stack.append(value)

        if len(stack) != 1:
            raise RuntimeError("Stack has %s items, should have 1" % len(stack))

        return stack[-1]

