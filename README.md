Expressions
===========

Lightweight arithmetic expression parser for creating simple arithmetic
expression compilers.

Part of the Data Brewery at http://databrewery.org

Sources
-------

Github: https://github.com/Stiivi/expressions

Requires at least Python 3.3. No other dependencies. No dependencies planned –
Python-only framework.

Use
---

Embed custom expression evaluation into your application. Example uses:

* variable checking compiler with allow/deny mechanism
* unification of functions and variables if your app provides multiple
  backends which might provide expression evaluation functionality
* compiler for custom object structures, such as for frameworks providing
  functional-programing like interface

Create a compiler that allows only certain variables:

    from expressions import Expression, ExpressionError

    class AllowingCompiler(object):
        def __init__(self, allow=None):
            self.allow = allow or []
        def compile_literal(self, literal):
            return repr(literal)
        def compile_variable(self, variable):
            if self.allow and variable not in self.allow:
                raise ExpressionError("Variable %s is not allowed" % variable)

            return variable

        def compile_operator(self, operator, op1, op2):
            return "(%s %s %s)" % (op1, operator, op2)
        def compile_function(self, function, args):
            arglist = ", " % args
            return "%s(%s)" % (function, arglist)

Allow only `a` and `b` variables:

    compiler = AllowingCompiler(allow=["a", "b"])

Try to compile and execute the expression:

    expr = Expression("a + b")
    result = expr.compile(compiler)

    a = 1
    b = 1
    print(eval(result))

This will fail, because only `a` and `b` are allowed, `c` is not:

    expr = Expression("a + c")
    result = expr.compile(compiler)

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

