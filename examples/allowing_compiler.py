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

compiler = AllowingCompiler(allow=["a", "b"])

expr = Expression("a + b")
result = expr.compile(compiler)

a = 1
b = 1
print(eval(result))

# This will fail, because only a and b are allowed
expr = Expression("a + c")
result = expr.compile(compiler)
