# -*- encoding: utf8 -*-

from .expressions import *

__all__ = (
            "SimpleCompiler",
        )

class SimpleCompiler(object):
    def __init__(self, allow=None, deny=None):
        """Creates a simple expression compiler producing an expression string
        that is executable by python's `eval()` function. `allow` is list of
        allowed identifiers – if present, identifiers have to be from the
        list. `deny` is a list of denied identifiers – if present, identifiers
        should not be from the list."""
        self.context = context or {}
        self.allow = allow or []
        self.deny = deny or []

    def compile_literal(self, literal):
        return literal

    def _assert_identifier(self, ident):
        if self.deny and ident in self.deny \
                or self.allow and ident not in self.allow:
                    raise ExpressionError("Unknown identifier '%s' "
                                            "(might be not allowed)" % ident)
    def compile_variable(self, variable):
        self._assert_identifier(variable)
        return str(variable)

    def compile_operator(self, operator, op1, op2):
        return "(%s %s %s)" % (op1, operator, op2)

    def compile_function(self, func, args):
        self._assert_identifier(func)
        arglist = ", ".join(args)
        return "%s(%s)" % (func, arglist)

