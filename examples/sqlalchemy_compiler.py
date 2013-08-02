from expressions import Compiler
from sqlalchemy import create_engine, MetaData, Table, Integer, Column
from sqlalchemy import sql

# Contents:
#
# 1. Expression compiler .............. line 18
# 2. Load example data ................ line 52
# 3. Compile and use the expression ... line 70


# A simple compiler that generates SQL Alchemy object structures from an
# arithmetic expression.
#
# Compilation context is a statement. Variables in the expression refer to the
# column names.

class SQLAlchemyExpressionCompiler(Compiler):
    def compile_literal(self, context, literal):
        """Compile a literal object – we just pass it along and let the
        SQLAlchemy functions deal with it"""
        return literal

    def compile_variable(self, context, variable):
        """Compile a variable – in our case it refers to a column of a
        SQL table or a SQL statement. The statement is our context of
        compilation."""
        return context.c[variable]

    def compile_operator(self, context, operator, op1, op2):
        """Return SQLAlchemy object construct using an operator."""

        if operator == "+":
            return op1 + op2
        elif operator == "-":
            return op1 - op2
        elif operator == "*":
            return op1 * op2
        elif operator == "/":
            return op1 / op2
        else:
            raise SyntaxError("Unknown operator '%s'" % operator)

# Some data:
data = [
        # id, transaction, amount
        [  1,          10,    100],
        [  2,          20,    150],
        [  3,          30,    200]
    ]

# 2. Create the example data table

engine = create_engine("sqlite:///")
metadata = MetaData(engine)

table = Table("Data", metadata,
                Column("id", Integer),
                Column("transactions", Integer),
                Column("amount", Integer)
            )

table.create()

# ... and load it with data
for row in data:
    engine.execute(table.insert().values(row))

#
# 3. The Expression
#
compiler = SQLAlchemyExpressionCompiler()

# Compile the expression within a context of the created table
#
selection = compiler.compile("(amount / transactions) * 2", table)
print("compiled selection type: %s" % type(selection))
print("compiled selection content: %s" % selection)

statement = sql.expression.select([selection], table)
print("SQL statement: %s" % statement)

result = statement.execute()
print("result: %s" % list(result))

