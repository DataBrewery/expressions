# -*- encoding: utf8 -*-
from expressions import Compiler

class AllowingCompiler(Compiler):
    def compile_literal(self, context, literal):
        return repr(literal)

    def compile_variable(self, context, variable):
        if context and variable.name not in context:
            raise Exception("Variable '%s' is not allowed" % variable)

        return variable

    def compile_binary(self, context, operator, op1, op2):
        return "(%s %s %s)" % (op1, operator, op2)

    def compile_function(self, context, function, args):
        arglist = ", " % args
        return "%s(%s)" % (function, arglist)


allowed_variables = ["a", "b"]

compiler = AllowingCompiler()

result = compiler.compile("a + b", allowed_variables)

a = 1
b = 1
print("Result is {}".format(eval(result)))

# This will fail, because only a and b are allowed
try:
    result = compiler.compile("a + c", allowed_variables)
except Exception as e:
    print("Compiler raised an exception (as expected): {}".format(e))
