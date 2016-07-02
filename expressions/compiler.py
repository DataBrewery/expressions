# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from .grammar import ExpressionParser, ExpressionSemantics
from grako.exceptions import FailedSemantics
from . import compat

__all__ = [
        "Compiler",
        "ExpressionInspector",
        "Variable",
        "Function",
        "BinaryOperator",
        "UnaryOperator",
        "Node",
        "inspect_variables"
    ]


class Node(object):
    pass

class Function(Node):
    def __init__(self, variable, args):
        self.reference = variable.reference
        self.name = variable.name
        self.args = args

    def __str__(self):
        return "{}({})".format(self.name, ", ".join(str(a) for a in self.args))

    def __repr__(self):
        return "{}({})".format(self.name, ", ".join(repr(a) for a in self.args))


class Variable(Node):
    def __init__(self, reference):
        """Creates a variable reference. Attributes: `reference` – variable
        reference as a list of variable parts and `name` as a full variable
        name. This object is passed to the `compile_variable()` and
        `compile_function()`"""

        self.reference = reference
        self.name = ".".join(self.reference)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Variable({.name})".format(self)

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return NotImplemented
        else:
            return self.name == other.name \
                    and self.reference == other.reference

    def __hash__(self):
        return hash(self.name)


class UnaryOperator(Node):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return "({0.operator} {0.operand})".format(self)

    def __repr__(self):
        return "Unary({0.operator!r}, {0.operand!r})".format(self)


class BinaryOperator(Node):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return "({0.left} {0.operator} {0.right})".format(self)

    def __repr__(self):
        return "Binary({0.left!r}, {0.operator!r}, {0.right!r})".format(self)


class _Result(object):
    """Wrapper class for compilation result. We need this to properly
    distinguish between our result and delegated results."""

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return "_Result({})".format(repr(self.value))


class _ExpressionSemantics(object):
    keywords = ['in', 'not', 'is', 'and', 'or']
    def __init__(self, compiler, context):
        self.compiler = compiler
        self.context = context

    def _default(self, ast, node_type=None, *args):

        if isinstance(ast, _Result):
            return ast

        if not node_type:
            return ast

        elif node_type == "unary":
            operator, operand = ast
            result = self.compiler.compile_unary(self.context,
                                                 operator,
                                                 operand.value)
        elif node_type == "binary":
            left, rest = ast
            left = left.value

            for op, right in rest:
                # Get the object's value
                right = right.value

                left = self.compiler.compile_binary(self.context, op,
                                                    left, right)
            result = left

        elif node_type == "binarynr":
            left, operator, right = ast
            result = self.compiler.compile_binary(self.context, operator,
                                                  left.value, right.value)
        else:
            raise Exception("Unknown node type '{}'".format(node_type))

        if isinstance(result, _Result):
            raise Exception("Internal compiler error - "
                            "unexpected _Result() object")
            # Variable is already wrapped

        return _Result(result)

    def variable(self, ast):
        # Note: ast is expected to be a _Result() from the `reference` rule
        value = ast.value
        if not isinstance(ast, _Result):
            import pdb; pdb.set_trace()
        result = self.compiler.compile_variable(self.context, value)
        return _Result(result)

    def reference(self, ast):
        return _Result(Variable(ast))

    def function(self, ast):
        ref = ast.ref.value
        args = [arg.value for arg in ast.args or []]
        result = self.compiler.compile_function(self.context, ref, args)

        return _Result(result)

    def NUMBER(self, ast):
        try:
            value = int(ast)
        except ValueError:
            value = float(ast)

        result = self.compiler.compile_literal(self.context, value)

        return _Result(result)

    def STRING(self, ast):
        # Strip the surrounding quotes
        value = compat.unicode_escape(compat.text_type(ast[1:-1]))

        result = self.compiler.compile_literal(self.context, value)
        return _Result(result)

    def NAME(self, ast):
        if ast.lower() in self.keywords:
            raise FailedSemantics("'{}' is a keyword.".format(ast))
        return ast


class Compiler(object):
    def __init__(self, context=None):
        """Creates an expression compiler with a `context` object. The context
        object is a custom object that subclasses might use during the
        compilation process for example to get variables by name, function
        objects. Context can be also used store information while compiling
        multiple expressions such as list of used attributes for analyzing
        requirements for query construction."""
        self.context = context

    def compile(self, text, context=None):
        """Compiles the `text` expression, returns a finalized object. """

        if context is None:
            context = self.context

        parser = ExpressionParser()

        result = parser.parse(text,
                 rule_name="arithmetic_expression",
                 comments_re="#.*",
                 ignorecase=False,
                 semantics=_ExpressionSemantics(self, context))

        # Result is of type _Result

        return self.finalize(context, result.value)

    def compile_literal(self, context, literal):
        """Compile a literal object such as number or a string. Default
        implementation returns a string or numeric object."""
        return literal

    def compile_variable(self, context, reference):
        """Compile variable `reference`. Default implementation returns
        `Variable` object."""
        return reference

    def compile_binary(self, context, operator, left, right):
        """Compile `operator` with operands `left` and `right`. Default
        implementation returns `BinaryOperator` object with attributes
        `operator`, `left` and `right`."""
        return BinaryOperator(operator, left, right)

    def compile_unary(self, context, operator, operand):
        """Called when an unary `operator` is encountered. Default
        implementation returns `UnaryOperator` object with attributes
        `operator` and `operand`"""
        return UnaryOperator(operator, operand)

    def compile_function(self, conext, function, args):
        """Called when a function call is encountered in the expression.
        `function` is a `Variable` object (you can use
        `str(function)` to get the full function name reference as string),
        `args` is a list of function arguments.
        """
        return Function(function, args)

    def finalize(self, context, obj):
        """Return final object as a result of expression compilation. By
        default returns the object returned by the last executed compilation
        method.

        Subclasses can override this method if they want to wrap the result
        object in another object or to finalize collected statement analysis."""
        return obj


class ExpressionInspector(Compiler):
    """Preprocesses an expression. Returns tuple of sets (`variables`,
    `functions`)"""
    def __init__(self):
        super(ExpressionInspector, self).__init__()

        self.variables = set()
        self.functions = set()

    def compile_variable(self, context, variable):
        self.variables.add(variable.name)
        return variable

    def compile_function(self, context, function, args):
        self.functions.add(function.name)
        return function

    def finalize(self, context, obj):
        return (self.variables, self.functions)

def inspect_variables(text):
    """Return set of variables in expression `text`"""
    inspector = ExpressionInspector()
    inspector.compile(text)
    return inspector.variables
