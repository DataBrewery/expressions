# -*- encoding: utf8 -*-

import unicodedata
from collections import namedtuple
import sys


__version__ = "0.1.2"


# Python 2 compatibility
#
PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
else:
    text_type = unicode
    string_types = (str, unicode)


# - end of compatibility -

class ExpressionError(Exception):
    """Raised by the expression compiler"""
    pass

__all__ = (
            "tokenize",
            "parse",
            "default_dialect",
            "register_dialect",
            "get_dialect",
            "unregister_dialect",

            "Compiler",
            "ExpressionError",
            "Dialect",
            "Operator",

            "RIGHT",
            "LEFT",
            "UNARY",
            "BINARY",

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

Token = namedtuple('Token', ["type", "value"])
Element = namedtuple('Element', ["type", "value", "argc"])
Operator = namedtuple("Operator", ["name", "precedence", "assoc", "type"])

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

LPAREN = u'('
RPAREN = u')'
LBRACKET = u'['
RBRACKET = u']'
COMMA = u','
COLON = u':'
SEMICOLON = u';'

# Unicode categories
# Source: http://www.unicode.org/Public/5.1.0/ucd/UCD.html#General_Category_Values

CAT_SEPARATOR = 'Z'
CAT_CONTROL = 'C'
CAT_NUMBER = 'N'
CAT_LETTER = 'L'
CAT_SYMBOL = 'S'
SUBCAT_MATH = 'm'

STRING_ESCAPE_CHAR = '\\'

UNARY = 1
BINARY = 2

RIGHT = 1
LEFT = 2

# Dialect
class Dialect(object):
    operators = None
    case_sensitive = None

    identifier_start_characters = None
    identifier_start_category = CAT_LETTER
    identifier_characters = None
    identifier_category = CAT_NUMBER + CAT_LETTER

    # Instance variables:
    # keyword_operators = []
    # operator_characters = ""
    # composed_operators = []

    def __init__(self):
        operators = {}
        for name, op in self.operators.items():
            if len(op) != 3:
                raise RuntimeError("Invalid specification of operator %s" % name)
            operator = Operator(name, op[0], op[1], op[2])
            operators[name] = operator
        opnames = operators.keys()
        self.operators = operators

        # Get keyword operators:
        self.keyword_operators = []
        for op in opnames:
            if all(unicodedata.category(c)[0] == CAT_LETTER for c in op):
                self.keyword_operators.append(op)

        plain_operators = [op for op in opnames if op not in self.keyword_operators]

        characters = u"".join(plain_operators)
        characters = u"".join(set(characters))
        self.operator_characters = characters

        composed_ops = [op for op in plain_operators if len(op) > 1]
        self.composed_operators = composed_ops

        self.identifier_start_characters = self.identifier_start_characters or u""
        self.identifier_start_category = self.identifier_start_category or u""
        self.identifier_characters = self.identifier_characters or u""
        self.identifier_category = self.identifier_category or u""

    def operator(self, name):
        return self.operators[name]

# Default Dialect
#
# Use the same structure as we require from dialect implementors, then cache
# prepared version after first use.
#
# The operator tuple is: (precedence, associativeness, type)
#
class default_dialect(Dialect):
    operators = {
        u"^": (1000, RIGHT, BINARY),
        u"*": (900, LEFT, BINARY),
        u"/": (900, LEFT, BINARY),
        u"%": (900, LEFT, BINARY),

        u"+":  (500, LEFT, BINARY),
        u"-":  (500, LEFT, UNARY | BINARY),

        u"&":  (300, LEFT, BINARY),
        u"|":  (300, LEFT, BINARY),

        u"<":  (200, LEFT, BINARY),
        u"<=": (200, LEFT, BINARY),
        u">":  (200, LEFT, BINARY),
        u">=": (200, LEFT, BINARY),
        u"!=": (200, LEFT, BINARY),
        u"==": (200, LEFT, BINARY),

        u"not": (120, LEFT, UNARY),
        u"and": (110, LEFT, BINARY),
        u"or":  (100, LEFT, BINARY),
    }
    case_sensitive = False

    identifier_start_characters = u"_"
    identifier_start_category = CAT_LETTER
    identifier_characters = u"_"
    identifier_category = CAT_NUMBER + CAT_LETTER

_dialects = {
        "default": default_dialect()
    }

def register_dialect(name, dialect):
    if name in _dialects:
        raise RuntimeError("Dialect %s already registered", name)
    _dialects[name] = dialect()

def get_dialect(dialect):
    if issubclass(dialect, Dialect):
        return dialect()
    else:
        return _dialects[dialect]

def unregister_dialect(name):
    del _dialects[name]

def tokenize(string, dialect="default"):
    """Break the `string` into tokens. Returns a list of tuples (`type`,
    `value`)"""

    reader = _StringReader(string, dialect)

    return reader.tokenize()

def parse(expression, dialect="default"):
    """Parses the `expressions` which might be a string or a list of tokens
    from `tokenize()`."""

    if isinstance(expression, string_types):
        tokens = tokenize(expression, dialect)

    else:
        tokens = expression

    parser = _Parser(dialect)
    return parser.parse(tokens)


class _StringReader(object):
    def __init__(self, string, dialect="default"):
        self.string = text_type(string)
        self.length = len(string)
        self.pos = 0
        self.char = None
        self.category = None
        self.subcategory = None

        self.dialect = get_dialect(dialect)

        # Prepare list of composed operatros

        if self.dialect.case_sensitive:
            self.keyword_operators = self.dialect.keyword_operators
        else:
            self.keyword_operators = [k.lower() for k in self.dialect.keyword_operators]

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

    # Python 3:
    def __bool__(self):
        return self.pos < self.length

    if PY2:
        def __nonzero__(self):
            return self.__bool__()

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

        if self.peek() == u".":
            token_type = FLOAT
            self.next()

            if self.peek_category() == CAT_NUMBER:
                self.next()
                self.consume(category=CAT_NUMBER)


        if self.at_end():
            return token_type

        if self.peek() in u"eE":
            token_type = FLOAT
            self.next()
            if self.peek() in u"+-":
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

            # FIXME: XXX
            if not self.char:
                raise Exception("No character at %s for '%s'" % (self.pos,
                    self.string ))

            # Integer
            if self.category == CAT_NUMBER:
                token_type = self.consume_numeric()

            # Identifier
            elif self.category in self.dialect.identifier_start_category \
                    or self.char in self.dialect.identifier_start_characters:

                token_type = IDENTIFIER

                self.next()

                self.consume(self.dialect.identifier_category,
                             self.dialect.identifier_characters)

            # Operator
            elif self.char in self.dialect.operator_characters:
                token_type = OPERATOR
                peek = self.peek()
                if peek:
                    composed = self.char + peek
                    if composed in self.dialect.composed_operators:
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


            tokens.append(self._coalesced_token(token_type, token))

            if not self:
                break

            self.next()

        return tokens

    def _coalesced_token(self, token_type, token):
        # TODO: treat escaped characters
        if token_type == STRING:
            token = token[1:-1]
        elif token_type == INTEGER:
            token = int(token)
        elif token_type == FLOAT:
            token = float(token)
        elif token_type == IDENTIFIER:
            if not self.dialect.case_sensitive:
                keyword = token.lower()
            else:
                keyword = token

            if keyword in self.dialect.keyword_operators:
                token_type = OPERATOR

        return Token(token_type, token)


class _Parser(object):
    def __init__(self, dialect="default"):
        dialect = get_dialect(dialect)
        self.operators = dialect.operators

        self.precedence = {}
        for name, op in dialect.operators.items():
            self.precedence[name] = op.precedence

    def parse(self, tokens):
        # Shunting-yard algorithm
        # Variable function arguments:
        # http://www.kallisti.net.nz/blog/2008/02/extension-to-the-shunting-yard-algorithm-to-allow-variable-numbers-of-arguments-to-functions/

        self.stack = []
        self.output = []
        # For variadic function:
        self.were_arguments = []
        self.argc = []
        # For deterining if an operator is unary
        self.was_value = False

        for i, token in enumerate(tokens):
            # The next_token is used only to identify whether identifier is a
            # variable name or a function call

            if i + 1 < len(tokens):
                next_token = tokens[i+1]
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

        return self.output

    def _parse_token(self, token):

        # Shunting-yard algorithm:
        #         http://en.wikipedia.org/wiki/Shunting-yard_algorithm

        # If the token is a number, then add it to the output queue.
        if token.type in LITERALS:
            self.output.append(Element(LITERAL, token.value, 0))

            if self.were_arguments:
                self.were_arguments[-1] = True

            self.was_value = True

        # ... same situation as above
        elif token.type == IDENTIFIER:
            self.output.append(Element(VARIABLE, token.value, 0))

            if self.were_arguments:
                self.were_arguments[-1] = True

            self.was_value = True

        # If the token is a function token, then push it onto the stack.
        elif token.type == FUNCTION:
            self.stack.append(Element(FUNCTION, token.value, 0))
            self.argc.append(0)

            if self.were_arguments:
                self.were_arguments[-1] = True
            self.were_arguments.append(False)

            self.was_value = False

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

            if self.were_arguments.pop():
                # Increase argument count
                self.argc.append(self.argc.pop() + 1)
            self.were_arguments.append(False)

            self.was_value = False

        # If the token is an operator, o1, then:
        elif token.type == OPERATOR:
            op1 = self.operators[token.value]

            # Determine if the operator should be considered unary:

            if op1.type == UNARY:
                is_unary = True
            elif (op1.type | UNARY) and not self.was_value:
                is_unary = True
            else:
                is_unary = False

            self.was_value = False

            if is_unary:
                self.stack.append(Element(OPERATOR, token.value, 1))

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

            self.was_value = False

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
                if self.were_arguments.pop():
                    argc += 1

                self.output.append(Element(FUNCTION, func.value, argc))

            # If the stack runs out without finding a left parenthesis, then
            # there are mismatched parentheses.

            # Right paren can be cosidered as a "closing of a composed value"
            self.was_value = True


class Compiler(object):
    dialect = "default"

    def __init__(self):
        """Initializes default compiler instance"""

        self.stack = []
        self.output = []

    def tokenize(self, string):
        """Parses the string and returns list of tokens."""
        tokens = []

        reader = _StringReader(string, dialect=self.dialect)

        try:
            tokens = reader.tokenize()
        except SyntaxError as e:
            raise SyntaxError("Syntax error at %s: %s" % (reader.pos, str(e)))

        return tokens

    def parse(self, expression):
        """Parse the `expression` which might be a string or a list of tokens
        created by the `tokenize()` method.

        Parser uses a modified Shunting-yard algorithm that supports variable
        number of function arguments.
        """

        if isinstance(expression, string_types):
            tokens = self.tokenize(expression)
        else:
            tokens = expression

        out = parse(tokens, dialect=self.dialect)
        return out

    def compile(self, expression, context=None):
        """Compile the `expression`. `context` is an optional object passed to
        the compiler methods.
        """

        # string -> tokens (follow compiler rules)
        # tokens -> infix (follow compiler rules)
        # infox -> object (follow context)

        # TODO: Use the context for parse
        output = self.parse(expression)

        stack = []
        for token in output:
            if token.type == LITERAL:
                value = self.compile_literal(context, token.value)

            elif token.type == VARIABLE:
                value = self.compile_variable(context, token.value)

            elif token.type == OPERATOR:
                if token.argc == 1:
                    op = stack.pop()
                    value = self.compile_unary(context, token.value, op)
                elif token.argc == 2:
                    op2 = stack.pop()
                    op1 = stack.pop()

                    value = self.compile_operator(context, token.value, op1, op2)
                else:
                    raise RuntimeError("Invalid operator argument count: %s" %
                                            token.argc)

            elif token.type == FUNCTION:
                if token.argc:
                    args = stack[-token.argc:]
                    del stack[-token.argc:]
                else:
                    args = []

                value = self.compile_function(context, token.value, args)

            else:
                raise RuntimeError("Unknown token type %s" % repr(token.type))

            stack.append(value)

        if len(stack) != 1:
            raise RuntimeError("Stack has %s items, should have 1" % len(stack))

        return self.finalize(context, stack[0])

    def compile_literal(self, context, literal):
        return None

    def compile_variable(self, context, variable):
        return None

    def compile_unary(self, context, operator, operand):
        return None

    def compile_operator(self, context, operator, op1, op2):
        return None

    def compile_function(self, context, function, args):
        return None

    def finalize(self, context, obj):
        """Give a chance to return final object. Default implementation returs
        the last compiled object."""
        return obj

