# -*- encoding: utf8 -*-

from .expressions import Compiler, Operator, RIGHT, LEFT, BINARY, UNARY

__all__ = (
            "SimpleCompiler",
        )

default_dialect = {
    "operators": (
        Operator("^",  1000, RIGHT, BINARY),
        Operator("*",   900, LEFT, BINARY),
        Operator("/",   900, LEFT, BINARY),
        Operator("%",   900, LEFT, BINARY),

        Operator("+",   500, LEFT, BINARY),
        Operator("-",   500, LEFT, UNARY | BINARY),

        Operator("^",   300, LEFT, BINARY),
        Operator("&",   300, LEFT, BINARY),
        Operator("|",   300, LEFT, BINARY),

        Operator("<",   200, LEFT, BINARY),
        Operator("<=",  200, LEFT, BINARY),
        Operator(">",   200, LEFT, BINARY),
        Operator(">=",  200, LEFT, BINARY),
        Operator("!=",  200, LEFT, BINARY),
        Operator("==",  200, LEFT, BINARY),

        Operator("not", 120, LEFT, UNARY),

        Operator("and", 110, LEFT, BINARY),
        Operator("or",  100, LEFT, BINARY),
    ),
    "keyword_operators": ("not", "and", "or")
}


class SimpleCompiler(object):
    def __init__(self, allow=None, deny=None):
        """Creates a simple expression compiler producing an expression string
        that is executable by python's `eval()` function. `allow` is list of
        allowed identifiers – if present, identifiers have to be from the
        list. `deny` is a list of denied identifiers – if present, identifiers
        should not be from the list."""
        super().__init__()

        self.allow = allow or []
        self.deny = deny or []

    def compile_literal(self, context, literal):
        return literal

    def _assert_identifier(self, context, ident):
        if self.deny and ident in self.deny \
                or self.allow and ident not in self.allow:
                    raise ExpressionError("Unknown identifier '%s' "
                                            "(might be not allowed)" % ident)
    def compile_variable(self, context, variable):
        self._assert_identifier(variable)
        return str(variable)

    def compile_operator(self, context, operator, op1, op2):
        return "(%s %s %s)" % (op1, operator, op2)

    def compile_function(self, context, func, args):
        self._assert_identifier(func)
        arglist = ", ".join(args)
        return "%s(%s)" % (func, arglist)

