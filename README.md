Expressions
===========

Lightweight arithmetic expression parser for creating simple arithmetic
expression compilers.

Part of the Data Brewery at http://databrewery.org

Sources
-------

Github: https://github.com/Stiivi/expressions

Works with Python 2.7 and Python 3.3. No other dependencies. No dependencies
planned – Python-only framework.

Use
---

Embed custom expression evaluation into your application. Example uses:

* variable checking compiler with allow/deny mechanism
* unification of functions and variables if your app provides multiple
  backends which might provide expression evaluation functionality
* compiler for custom object structures, such as for frameworks providing
  functional-programing like interface

Create a compiler that allows only certain variables. The list of allowed
variables is provided in the compilation context:

    from expressions import Compiler, ExpressionError

    class AllowingCompiler(Compiler):
        def compile_literal(self, context, literal):
            return repr(literal)

        def compile_variable(self, context, variable):
            if context and variable not in context:
                raise ExpressionError("Variable %s is not allowed" % variable)

            return variable

        def compile_operator(self, context, operator, op1, op2):
            return "(%s %s %s)" % (op1, operator, op2)

        def compile_function(self, context, function, args):
            arglist = ", " % args
            return "%s(%s)" % (function, arglist)

Allow only `a` and `b` variables:

    compiler = AllowingCompiler()

    allowed_variables = ["a", "b"]

Try to compile and execute the expression:

    result = compiler.compile("a + b", allowed_variables)

    a = 1
    b = 1
    print(eval(result))

This will fail, because only `a` and `b` are allowed, `c` is not:

    result = compiler.compile("a + c", allowed_variables)

Writing a compiler
==================

To write a custom compiler subclass a `Compiler` class and implement the
following methods:

* `compile_literal` taking a number or a string object
* `compile_variable` taking a variable name
* `compile_operator` taking a binary operator and two operands
* `compile_unary` taking an unary operator and one operand
* `compile_function` taking a function name and list of arguments

Template:

    class MyCompiler(Compiler):
        def compile_literal(self, context, literal):
            pass
        def compile_variable(self, context, variable):
            pass
        def compile_operator(self, context, operator, op1, op2):
            pass
        def compile_unary(self, context, operator, operand):
            pass
        def compile_function(self, context, function, args):
            pass

To-do
-----

Stay lightweight and simple.

License
-------

Expressions framework is licensed under the MIT license.

For more information see the LICENSE file.


Author
------

Stefan Urbanek, stefan.urbanek@gmail.com, Twitter: @Stiivi

