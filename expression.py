# -*- encoding: utf8 -*-

import unicodedata
from collections import namedtuple

__all__ = (
            "parse",

            "TINTEGER",
            "TFLOAT",
            "TSTRING",
            "TIDENTIFIER",

            "TOPERATOR",
            "TLPAR",
            "TRPAR",
            "TLBRACKET",
            "TRBRACKET",
            "TCOMMA",
            "TCOLON",
            "TSEMICOLON",
        )

# Tokens:

TINTEGER = 'i'    # 10
TFLOAT = 'f'      # 10.1
TSTRING = 's'     # "abc" or 'abc'
TOPERATOR = 'o'   # + - * /
TIDENTIFIER = 'l' # l as in Label

TLPAR = '('
TRPAR = ')'
TLBRACKET = '['
TRBRACKET = ']'
TCOMMA = ','
TCOLON = ':'
TSEMICOLON = ';'

STRING_TOKEN = 1

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
        token_type = TINTEGER
        self.consume(category=CAT_NUMBER)

        if self.peek() == ".":
            token_type = TFLOAT
            self.next()

            if self.peek_category() == CAT_NUMBER:
                self.next()
                self.consume(category=CAT_NUMBER)


        if self.at_end():
            return token_type

        if self.peek() in "eE":
            token_type = TFLOAT
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

    def parse(self):
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

                token_type = TIDENTIFIER

                if self.char in IDENTIFIER_START_CHARS:
                    self.next()
                self.consume(CAT_IDENTIFIER, IDENTIFIER_START_CHARS)

            # Operator
            elif self.char in OPERATOR_CHARS:
                token_type = TOPERATOR
                peek = self.peek()
                if peek:
                    composed = self.char + peek
                    if composed in COMPOSED_OPERATORS:
                        self.next()

            elif self.char == "'" or self.char == '"':
                token_type = TSTRING
                self.consume_string(self.char)
            elif self.char == '(':
                token_type = TLPAR
            elif self.char == ')':
                token_type = TRPAR
            elif self.char == '[':
                token_type = TLBRACKET
            elif self.char == ']':
                token_type = TRBRACKET
            elif self.char == ',':
                token_type = TCOMMA
            elif self.char == ':':
                token_type = TCOLON
            elif self.char == ';':
                token_type = TSEMICOLON
            else:
                raise SyntaxError("Unknown character %s, category %s%s" %
                                            (repr(self.char),
                                             self.category,
                                             self.subcategory))

            token = self.string[start:self.pos+1]

            # TODO: treat escaped characters
            if token_type == TSTRING:
                token = token[1:-1]

            tokens.append(Token(token, token_type))

            if not self:
                break

            self.next()

        return tokens


Token = namedtuple('Token', ["value", "type"])

def parse(string):
    """Parses the string and returns list of tokens."""
    tokens = []

    reader = _StringReader(string)

    try:
        tokens = reader.parse()
    except SyntaxError as e:
        raise SyntaxError("Syntax error at %s: %s" % (reader.pos, str(e)))

    return tokens

