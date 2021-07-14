from typing import *
import regex # different from re!

r = r"""^ *-?[0-9][0-9,\.]* *$|^ *[A-z][A-z0-9-?\/\\!]* *$|^(\((?:[^()]++|(?1))*\))$"""
"""        NUMBERS            |  LITERALS                 |  S-EXPRS (even nested!) """

rex = regex.compile(r, regex.M)

def extract_expressions(s: str) -> List:
    """
    Split a string, made up of multiple lines, into separate
    s-exprs.
    """
    s = regex.sub(r';;.*', "", s.strip()) # rimuove i commenti

    exprs = list()
    for match in regex.finditer(rex, s):
        start, end = match.span()
        exprs.append(s[start:end].strip())

    return exprs

#########################################

import enum
class Print(enum.Enum):
    NOTHING = 0
    FINAL = 1
    ALL = 2

##########################################
import inspect

def deduce_arity(foo: Callable) -> int:
    if foo.__class__.__name__ == "Procedure":
        return len(foo.parms)
    
    sig = inspect.signature(foo)
    return len(sig.parameters)

###########################################

def replace_but_not_inside_quotes(old: chr, new: chr, s: str) -> str:
    new_s = str()
    in_quotes = False
    
    for c in s:
        if c == "\"":
            in_quotes = not in_quotes
            new_s += c
            continue

        if c == old:
            if not in_quotes:
                new_s += new
            else:
                new_s += c
            continue

        new_s += c
                
    return new_s
