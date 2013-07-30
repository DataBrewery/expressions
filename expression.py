# -*- encoding: utf8 -*-

import unicodedata
from collections import namedtuple

__all__ = (
            "tokenize",
            "Expression",

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
COMPOSED_OPERATORS = ( "!=", "==", "<=", ">=" )
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

            tokens.append(Token(token_type, token))

            if not self:
                break

            self.next()

        return tokens


Token = namedtuple('Token', ["type", "value"])

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

Operator = namedtuple("Operator", ["name", "precedence", "type"])

optable = (
    Operator("**", 1000, BINARY),
    Operator("*", 900, BINARY),
    Operator("/", 900, BINARY),
    Operator("%", 900, BINARY),

    Operator("+", 500, BINARY),
    Operator("-", 500, UNARY | BINARY),

    Operator("&", 300, UNARY),
    Operator("^", 300, BINARY),
    Operator("|", 300, BINARY),

    Operator("<", 200, BINARY),
    Operator("<=", 200, BINARY),
    Operator(">", 200, BINARY),
    Operator(">=", 200, BINARY),
    Operator("!=", 200, BINARY),
    Operator("==", 200, BINARY),
    Operator("in", 200, BINARY),
    Operator("is", 200, BINARY),
    Operator("not in", 200, BINARY),
    Operator("is not", 200, BINARY),

    Operator("not", 120, UNARY),

    Operator("and", 110, BINARY),
    Operator("or", 100, BINARY),
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

        self.stack = []
        self.output = []

        for i, token in enumerate(self.tokens):
            # The next_token is used only to identify whether identifier is a
            # variable name or a function call

            if i + 1 < len(self.tokens):
                next_token = self.tokens[i+1]
                if token.type == IDENTIFIER and next_token.type == LPAREN:
                    token = Token(FUNCTION, token.value)

            self.parse_token(token)

        while(self.stack):
            token = self.stack.pop()
            if token.type == RPAREN:
                raise SyntaxError("Missing right parethesis")
            self.output.append(token)

    def parse_token(self, token):

        if token.type in LITERALS:
            self.output.append( Token(LITERAL, token.value) )

        elif token.type == IDENTIFIER:
            self.output.append( Token(VARIABLE, token.value) )

        elif token.type == FUNCTION:
            self.stack.append( Token(FUNCTION, token.value) )

        elif token.type == COMMA:
            while(self.stack):
                if self.stack[-1].type == LPAREN:
                    break
                self.output.append(self.stack.pop())

        elif token.type == OPERATOR:
            while(self.stack):
                op2 = self.stack[-1]
                if op2.type != OPERATOR:
                    break

                p1 = self.precedence[token.value]
                p2 = self.precedence[op2.value]

                # TODO: store this in the operator info, for the time being we
                # assume all operators to be left associative
                is_lassoc = True

                if not ((is_lassoc and p1 == p2) or p1 < p2):
                    break

                self.output.append(self.stack.pop())

            self.stack.append(Token(OPERATOR, token.value))

        elif token.type == LPAREN:
            self.stack.append( Token(LPAREN, '(') )

        elif token.type == RPAREN:
            while(self.stack):
                if self.stack[-1].type == LPAREN:
                    break
                self.output.append(self.stack.pop())

            # pop the left parenthesis
            self.stack.pop()
            if self.stack and self.stack[-1].type == FUNCTION:
                self.output.append(self.stack.pop())


