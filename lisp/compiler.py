from typing import List, Callable, Dict, Tuple,  _CallableGenericAlias
import socket
import shlex
import threading
import os
import random

from lisp.utils import *

class Symbol(str): pass

Number = (int, float)     # A Scheme Number is implemented as a Python int or float
Atom   = (Symbol, Number) # A Scheme Atom is a Symbol or Number
List   = list             # A Scheme List is implemented as a Python list
Exp    = (Atom, List)     # A Scheme expression is an Atom or List
Env    = dict             # A Scheme environment (defined below) 
                          # is a mapping of {variable: value}

class LispError(Exception): pass
class LispParseError(LispError): pass
class LispSymbolError(LispError): pass

def tokenize(chars: str) -> list:
    "Convert a string of characters into a list of tokens."
    return shlex.split(
        replace_but_not_inside_quotes('(', ' ( ',
          replace_but_not_inside_quotes(')', ' ) ',
            replace_but_not_inside_quotes("'", " ` ", chars))),
        posix=False
    )
            

def parse(program: str) -> Exp:
    "Read a Scheme expression from a string."
    return read_from_tokens(tokenize(program))

def read_from_tokens(tokens: list) -> Exp:
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise LispParseError('unexpected EOF')

    token = tokens.pop(0)

    if token == "`":
        return ["quote", read_from_tokens(tokens)]
    if token.startswith("\""):
        return ["string", token[1:-1]]
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0) # pop off ')'
        return L
    if token == ')':
        raise LispParseError('unexpected )')
    
    return atom(token)


def atom(token: str) -> Atom:
    "Numbers become numbers; every other token is a symbol."
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            # if token[0] == "\"":
            #     return ["string", token] #TODO?
            # else:
            return Symbol(token)

##################################

class Context(dict):
    def __init__(self, parms: list, args: list, outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def depth(self, acc=0):
        if self.outer is None:
            return acc
        return self.outer.depth(acc=acc+1)
        
    def add(self, k, v):
        self.update(zip([k], [v]))

    def outermost_add(self, k, v):
        if self.outer is None:
            self.add(k, v)
        else:
            self.outer.outermost_add(k, v)
        
    def find(self, var):
        "Find the innermost Ctx where var appears."
        try:
            return self[var] if (var in self) else self.outer.find(var)
        except AttributeError as e:
            print(f"Coulnd't find {var}")
            raise LispSymbolError(str(e)) from e
        
class Procedure():
    "A user-defined Scheme procedure."
    def __init__(self, parms, body, ctx, _help=None, debug=False):
        self.parms, self.body, self.ctx = parms, body, ctx
        self.help = None if _help is None else eval_free(_help, ctx, debug=debug)
        self.debug = debug
    def __call__(self, *args):
        return eval_free(self.body, Context(self.parms, args, outer=self.ctx), debug=self.debug)
    

################################
import time

def print_help(foo: Union[Callable, Procedure]):
    if isinstance(foo, Procedure):
        if foo.help is None:
            return False

        return foo.help

    return False

def read_file(fpath: str) -> str:
    with open(fpath, "r") as f:
        return ["string", f.read()]
def write_file(fpath: str, data: str) -> str:
    with open(fpath, "w") as f:
        return f.write(data)
def append_to_file(fpath:str, data: str):
    with open(fpath, "a") as f:
        return f.write(data)    
def import_func(fpath):
    pass # TODO
    
def get_type(obj):
    if isinstance(obj, (int, float)):
        return Symbol("number")
    if isinstance(obj, Symbol):
        return Symbol("symbol")
    if isinstance(obj, str):
        return Symbol("string")
    if isinstance(obj, list):
        return Symbol("lst")

def foldl(func, acc, l):
    for x in l:
        acc = func(x, acc)
    return acc
def repeat_until(func, acc, cond):
    while not cond(acc):
        acc = func(acc)
    return acc

import functools, operator as op
context_base_simple = {
    "t": True,
    "nil": False,
    "and": (lambda x, y: x and y),
    "or": (lambda x, y: x or y),
    "not": (lambda x: not x),

    "=": (lambda x, y: x == y),
    "!=": (lambda x, y: x != y),
    ">=": (lambda x, y: x >= y),
    ">": (lambda x, y: x > y),
    "<=": (lambda x, y: x <= y),
    "<": (lambda x, y: x < y),

    # "+": (lambda *ns: sum(ns)),
    "+": (lambda *ns: functools.reduce(op.add, ns)),
    "-": (lambda x,y: x-y),
    "*": (lambda *ns: functools.reduce(op.mul, ns)),
    "**": (lambda x,y: x**y),
    "++": (lambda x: x+1),
    "*2": (lambda x: x*2),
    "mod": (lambda x,y: x % y),
    "/": (lambda x,y: x / y),

    "cons": lambda x,xs: [x] + xs,
    "head": lambda xs: Symbol("err-empty-list") if len(xs) == 0 else xs[0],
    "tail": lambda xs: xs[1:],
    "append": lambda x,xs: xs + [x],
    "nth": lambda l, n: l[n] if 0 <= n <= len(l) else Symbol("err-empty-list"),
    "is-list?": lambda x: isinstance(x, list),

    "compose": lambda f1, f2: lambda x: f1 ( f2 (x)),
    
    "map": lambda f,l: [f(x) for x in l],
    "fold": foldl,
    "repeat-until": repeat_until,
    
    "time": time.time,
    "sleep": time.sleep,
    "random": random.randint,
    "help": print_help,
    "import": import_func,
    
    "read": lambda s: parse(input(s)),
    "read-with-macro": lambda s, m: m(parse(input(s))),
    "show": lambda x: str(x),

    "pwd": os.getcwd(),
    "read-file": read_file,
    "write-file": write_file,
    "append-to-file": append_to_file,

    "type?": get_type,
    "atom?": lambda x: isinstance(x, (int, float, str, Symbol)) # TODO: str pu?? essere stringa o simbolo!
}

context_base = Context(context_base_simple.keys(), context_base_simple.values())

#######################################

def ast_to_str(ast: List) -> str:
    """
    Converts an AST to string (basically upnarsing)
    """
    if not isinstance(ast, list):
        return str(ast)

    return f"({ast[0]} " + " ".join(ast_to_str(x) for x in ast[1:]) + ")"

import logging

logger = logging.getLogger("[EVAL]")

def eval_free(ast: List, context: dict, debug=False):
    while True:
        # print(ast)
        
        if debug:
            print(ast)

        if isinstance(ast, Symbol):
            return context.find(ast)

        if isinstance(ast, (int, float)): #TODO: ma era questo?
            return ast

        if isinstance(ast, str): #TODO: ma era questo?
            return ast

        if isinstance(ast, list):
            if len(ast) == 0: # '() o (list)
                return []

            # print(f"DEPTH: {context.depth()}")
                
            if ast[0] == "quote":
                return ast[1]

            if ast[0] == "string":
                return ast[1]

            elif ast[0] == "list":
                return [eval_free(el, context, debug=debug) for el in ast[1:]]
            
            if ast[0] == "lambda":
                if len(ast[1:]) == 3:
                    variables = ast[1]
                    _help = ast[2]
                    body = ast[3]
                elif len(ast[1:]) == 2:
                    _help = None
                    variables = ast[1] 
                    body = ast[2]
                else:
                    raise LispError(f"lambda expects 2/3 arguments, were given {len(ast[1:])}")

                return Procedure(variables, body, context, _help=_help, debug=debug)

            if ast[0] == "define":
                #funziona per non-ricorsive
                context.outermost_add(ast[1], eval_free(ast[2], context, debug=debug)) 
                return ast[1]

            if ast[0] == "cond":
                for clause in ast[1:]:
                    if eval_free(clause[0], context, debug=debug):
                        ast = clause[1]
                        break
                else:
                    assert eval_free(ast[-1][0], context, debug=debug), f"{ast[-1][0]} should evaluate to T!"
                    print("WARNING")
                    return 

            elif ast[0] == "if":
                if eval_free(ast[1], context, debug=debug):
                    ast = ast[2]
                else:
                    ast = ast[3]

            elif ast[0] == "begin":
                for x in ast[1:-1]:
                    eval_free(x, context, debug=debug)
                ast = ast[-1]

            elif ast[0] == "curry":
                ast = ast[1]
                
                num_declared_args = len(ast) - 1

                symbol_eval = eval_free(ast[0], context, debug=debug)
                function_arity = deduce_arity(
                    symbol_eval
                )

                alfabeto = "abcdefghij"
                ast = [
                    "lambda",
                    [Symbol(c) for c in alfabeto[:function_arity-num_declared_args]],
                    ast + [Symbol(c) for c in alfabeto[:function_arity-num_declared_args]]
                ]

                
            elif ast[0] == "let":   
                # Per esempio, se ho
                # 
                #   (let foo (lambda (x) (if (= x 0) 0 (let-rec (- x 1)))))
                # 
                # Il primo passo ?? fare EVAL sulla lambda:
                inner_ctx = Context([], [], context)

                MULTI_LET = len(ast) == 3

                if MULTI_LET:
                    for let_clause in ast[1]:

                        let_clause_body = eval_free(let_clause[1], inner_ctx, debug=debug)

                        # Se il corpo del let-rec ?? effettivamente una procedura (e non
                        # ad es. un numero), essa potrebbe essere ricorsiva.
                        # Per cui, aggiungi nel contesto della procedura
                        # un binding a s?? stessa, aka. aggiungi al contesto della procedura
                        # la coppia {foo : Procedure<foo, body=...,>}
                        if isinstance(let_clause_body, Procedure):
                            let_clause_body.ctx.add(let_clause[0], let_clause_body)

                        inner_ctx.add(let_clause[0], let_clause_body)

                else:
                    let_clause_body = eval_free(ast[2], inner_ctx, debug=debug)

                    if isinstance(let_clause_body, Procedure):
                        let_clause_body.ctx.add(ast[1], let_clause_body)

                    inner_ctx.add(ast[1], let_clause_body)

                return eval_free(ast[2] if MULTI_LET else ast[3], inner_ctx, debug=debug)


            elif ast[0] == "debug":
                if ast[1] == "ctx":
                    print(context)
                    return "ok"
                if ast[1] == "break":
                    breakpoint()
                    return "ok"
                if ast[1] == "stack":
                    i, temp = 0, context

                    while temp != None:
                        print(temp)
                        temp = temp.outer
                        i += 1
                    breakpoint()
                    print(i)
                    return "ok"
                if ast[1] == "t":
                    debug=True
                    return "ok"
                if ast[1] == "f":
                    debug=False
                    return "ok"

            elif ast[0] == "eval":
                # ast = eval_free(ast[1], context, debug=debug)
                return eval_free(ast[1], context, debug=debug)
                
            elif ast[0] == "evalS":
                if ast[1][0] == "string":
                    # ast = eval_free(parse(ast[1][1]), context, debug=debug)
                    return eval_free(parse(ast[1][1]), context, debug=debug)
                else:
                    s = eval_free(ast[1], context, debug=debug)
                    ast = ["evalS", s]
                    
            elif ast[0] == "print":
                eval_body = eval_free(ast[1], context, debug=debug)
                print(eval_body)
                return eval_body

            else:
                eval_exprs = [eval_free(piece, context, debug=debug) for piece in ast]
                # if debug:
                #     breakpoint()
                eval_func  = eval_exprs[0]

                if isinstance(eval_func, Procedure):
                    ast = eval_func.body
                    context = Context(eval_func.parms, eval_exprs[1:],
                                      Context(eval_func.ctx.keys(),
                                              eval_func.ctx.values(),
                                              context))
                else:
                    return eval_func(*eval_exprs[1:])

        else:
            raise LispError("Unknwown type")


def evalS(program, context=None, debug=False):
    ast = parse(program)
    if context is None:
        return eval_free(ast, context_base, debug=debug)
    return eval_free(ast, context, debug=debug)


def eval_program(program, ctx=None, what_to_print=Print.ALL, debug=False, returns="ctx"):
    import copy

    lines = extract_expressions(program)
    ctx = copy.deepcopy(context_base) if ctx is None else ctx

    partial_results = list()
    for expr in lines:
        result = eval_free(parse(expr), ctx, debug=debug)

        if what_to_print == Print.ALL:
            print(expr)
            print(" = " + str(result) + "\n")

        partial_results.append(result)

    if returns == "ctx":
        return ctx
    
    if returns == "val":
        if what_to_print.value > 0:
            print(partial_results[-1])
        return partial_results[-1]

    raise LispError(f"`returns` parameter must be either ctx or val (given: {returns}")

############################################

import readline

def ev(program: str, what_to_print=Print.ALL, returns="ctx"):
    user_library = open("lisp/stdlib.lisp", "r").read()
    userctx = eval_program(user_library, what_to_print=what_to_print)
    return eval_program(program, userctx, what_to_print=what_to_print, returns=returns)
    
def repl(debug=False, fpath=None):
    import traceback

    if fpath is not None:
        with open(fpath, "r") as f:
            readed = f.read()
    else:
        readed = ""
        
    userctx = ev(readed, what_to_print=Print.FINAL)
    while (inp := input("?? ")) != "q":
        try:
            eval_program(inp, userctx, what_to_print=Print.ALL, debug=debug)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


def mcirc():
    ev("(metacircular (list if-macro-checker for-macro-sub))")
    
# repl()
# mcirc()
