Expressions
===========

Arithmetic expression parser library.  Embed customized expression evaluation
into your application or library. Example uses:

* precompiler that checks for allowed and denied identifiers in an expression
* have a common expression language through your application regardless of the
  backend languages
* compile arithmetic expression to any other expression tree (semantic), for
  example [SQLAlchemy](http://docs.sqlalchemy.org/en/rel_0_7/core/expression_api.html) expression objects


Part of the [Data Brewery](http://databrewery.org)

Installation
------------

Install using pip:

    pip install expressions

Expressions sources are available at [Github](https://github.com/Stiivi/expressions)

Works with Python 2.7 and Python 3.3. Uses [Grako](https://bitbucket.org/apalala/grako).

Example
-------

Here is an example compiler that allows only certain variables. The list of
allowed variables is provided in the compilation context:

```python
    from expressions import Compiler, ExpressionError

    class AllowingCompiler(Compiler):
        def compile_literal(self, context, literal):
            return repr(literal)

        def compile_variable(self, context, variable):
            if context and variable not in context:
                raise ExpressionError("Variable %s is not allowed" % variable)
 
            return variable

        def compile_binary(self, context, operator, op1, op2):
            return "(%s %s %s)" % (op1, operator, op2)

        def compile_function(self, context, function, args):
            arglist = ", " % args
            return "%s(%s)" % (function, arglist)
```

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

Syntax
======

Example expressions:

```sql
    1 + 1
    (a + b) ^ 2
    sum(amount) / count()
    date.year = 2010 and amount > 10
```

* Binary arithmetic operators: `+`, `-`, `*`, `/`, `%` (modulo), `^` (power)
* Binary comparison operators: `<`, `<=`, `=`, `>=`, `>`, `in`, `is`
* Binary bit-wise operators: `|` (or), `&` (and), `<<` (shift left), `>>` (shift right)
* Binary logical operators: `and`, `or`
* Unary operators: `+`, `-`, `~` (bit-wise not)

* Function call: `function_name(arg1, arg2, ...)`

*Variable* and *function* names are either regular identifiers or identifiers
separated by `.`. There is no value dereference and the dot `.` is just
namespace composition operator for variable names. Example variable names:
`amount`, `date.year`, `product.name`.

The suggested meaning of the operators is based mostly on the
[PostgreSQL operators](http://www.postgresql.org/docs/9.0/static/functions.html)

Writing a compiler
==================

To write a custom compiler subclass a `Compiler` class and implement all of
some of the following methods:

* *compile_function(context, reference, args)* – compile a function call. The
  `reference` is the same kind of object as passed to the
  *compile_variable()*, `args` is list of function arguments. Default
  implementation returns an object with attributes `reference` and `args`
* *compile_binary(context, operator, left, right)* – compile a binary
  operator `operator` with two operands `left` and `right`. Default
  implementation returns an object with attributes `operator`, `left` and `right`
* *compile_unary(context, operator, operand)* – compile a unary `operator` with
  a single `operand`. Default implementation returns an object with attributes
  `operator` and `operand`.
* *compile_variable(context, variable)* – compile a variable reference
  `variable` which is an object with properties `name` and `reference`. `name`
  is the full variable name (joined with `.`), `reference` is a list of
  variable name components. Return value should be either evaluated variable
  as a constant or some other useful variable reference.
* *compile_literal(context, literal)* – compile an integer, float or a string
  object `literal`. Default implementation just passes the argument. You
  rarely need to override this method.
* *finalize(context, object)* – return the final compilation result.


When compiling function arguments or operator operands you should check
whether they are literals or instances of a `Variable`. For example:

```python
    def compile_function(context, reference, args):
        # Assume that the context is a dictionary with variables and functions

        values = []
        for arg in args:
            if isinstance(arg, Variable):
                value = context[arg.name]
            else:
                value = arg
            values.append(value)

        function = context[reference.name]

        return function(*args)
```

Example compiler: Identifier Preprocessor

The following compiler is included in the library:

```python
    class IdentifierPreprocessor(Compiler):
        def __init__(self):
            super(IdentifierPreprocessor, self).__init__()

            self.variables = set()
            self.functions = set()

        def compile_variable(self, context, variable):
            self.variables.add(variable)
            return variable

        def compile_function(self, context, function, args):
            self.functions.add(function)
            return function
```

Classes
=======

The following classes are provided by the library:

* *Compiler* – core compiler class that generates default structure,
  `compile_*` methods can be overriden to generate custom results
* *IdentifierPreprocessor* – a *Compiler* subclass with two attributes
  `variables` and `functions` containing list of `Variable` objects collected
  from the compiled expression. Can be used for validation or preparation of
  variables


License
-------

Expressions framework is licensed under the MIT license.

For more information see the LICENSE file.


Author
------

Stefan Urbanek, stefan.urbanek@gmail.com, Twitter: @Stiivi


