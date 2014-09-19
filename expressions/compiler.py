# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from .grammar import ExpressionParser, ExpressionSemantics
from grako.exceptions import FailedSemantics

__all__ = [
        "Compiler",
        "Literal",
        "Variable",
        "Function",
    ]


class ASTNode(object):
    pass

class Atom(ASTNode):
    pass

class Function(Atom):
    def __init__(self, variable, args):
        self.reference = variable.reference
        self.name = variable.name
        self.args = args

    def __str__(self):
        return "{}({})".format(self.name, ", ".join(str(a) for a in self.args))

    def __repr__(self):
        return "{}({})".format(self.name, ", ".join(repr(a) for a in self.args))


class Variable(Atom):
    def __init__(self, reference):
        self.reference = reference
        self.name = ".".join(self.reference)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Variable({.name})".format(self)


class Literal(Atom):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Literal({.value})".format(self)


class UnaryOperator(ASTNode):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return "({0.operator} {0.operand})".format(self)

    def __repr__(self):
        return "Unary({0.operator!r}, {0.operand!r})".format(self)


class BinaryOperator(ASTNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return "({0.left} {0.operator} {0.right})".format(self)

    def __repr__(self):
        return "Binary({0.left!r}, {0.operator!r}, {0.right!r})".format(self)


class Node(object):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return "Node({})".format(repr(self.value))


class _ExpressionSemantics(object):
    keywords = ['in', 'not', 'is', 'and', 'or']
    def __init__(self, compiler, context):
        self.compiler = compiler
        self.context = context

    def _default(self, ast, node_type=None, *args):
        print("-->[{}, {}] {}".format(node_type, args, ast))

        if isinstance(ast, Node):
            print("<-O {} {}".format(type(ast.value), ast))
            return ast

        if not node_type:
            print("<-N  {}".format(ast))
            return ast

        elif node_type == "unary":
            operator, operand = ast
            result = self.compiler.compile_unary(self.context,
                                                 operator,
                                                 operand.value)
        elif node_type == "binary":
            left, rest = ast
            left = left.value

            ops = rest[0::2]
            rights = rest[1::2]

            for op, right in zip(ops, rights):
                # Get the object's value
                right = right.value

                left = self.compiler.compile_operator(self.context,
                                                      op,
                                                      left,
                                                      right)
            result = left

        elif node_type == "binarynr":
            left, operator, right = ast
            result = self.compiler.compile_operator(self.context,
                                                    operator,
                                                    left.value,
                                                    right.value)
        else:
            raise Exception("Unknown node type '{}'".format(node_type))

        print("<--  {}".format(ast))
        if isinstance(result, Node):
            import pdb; pdb.set_trace()
        return Node(result)

    def variable(self, ast):
        print("--- variable: {}".format(ast))
        import pdb; pdb.set_trace()
        value = ast
        result = self.compiler.compile_variable(self.context, value)
        return Node(result)

    def reference(self, ast):
        print("--- ref: {}".format(ast))
        return Node(Variable(ast))

    def function(self, ast):
        print("--- function: {}".format(ast))
        ref = ast.ref.value
        args = [arg.value for arg in ast.args]
        result = self.compiler.compile_function(self.context, ref, args)

        return Node(result)

    def NUMBER(self, ast):
        print("--- number: {}".format(ast))
        try:
            value = int(ast)
        except ValueError:
            value = float(ast)

        result = self.compiler.compile_literal(self.context, value)

        return Node(result)

    def STRING(self, ast):
        print("--- string: {}".format(ast))
        value = str(ast)

        result = self.compiler.compile_literal(self.context, value)
        return Node(result)

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

        # Result is of type Node

        return self.finalize(context, result.value)

    def compile_literal(self, context, literal):
        """Compile a literal object such as number or a string. Default
        implementation returns `Literal` object with attribute `value`."""
        return Literal(literal)

    def compile_variable(self, context, reference):
        """Compile variable `reference`. Default implementation returns
        `Variable` object."""
        return Variable(reference)

    def compile_operator(self, context, operator, left, right):
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

if __name__ == "__main__":
    compiler = Compiler()
    result = compiler.compile('a < 10 < 20 + 20')
    print("RESULT: ", result)
    print("REPR  : ", repr(result))
