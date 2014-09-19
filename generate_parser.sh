# Generate grammar parser

GRAMMAR=expressions/grammar.ebnf
PARSER=expressions/grammar.py
NAME=Expression

python -m grako -o $PARSER -m $NAME $GRAMMAR
