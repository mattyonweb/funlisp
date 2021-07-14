from typing import List, Callable, Dict, Tuple,  _CallableGenericAlias
import socket
import shlex
import threading

from lisp.utils import *

Symbol = str              # A Scheme Symbol is implemented as a Python str
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
            return Symbol(token)

##################################

class Context(dict):
    def __init__(self, parms: list, args: list, outer=None):
        self.update(zip(parms, args))
        self.outer = outer
        
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
            breakpoint()
            raise LispSymbolError(str(e))
        
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
    
context_base_simple = {
    "t": True,
    "nil": False,
    "and": (lambda x, y: x and y),
    "or": (lambda x, y: x or y),
    "not": (lambda x: not x),
    "->": (lambda x, y: (not x) or y),

    "=": (lambda x, y: x == y),
    "!=": (lambda x, y: x != y),
    ">=": (lambda x, y: x >= y),
    ">": (lambda x, y: x > y),
    "<=": (lambda x, y: x <= y),
    "<": (lambda x, y: x < y),

    "+": (lambda x,y: x+y),
    "-": (lambda x,y: x-y),
    "*": (lambda x,y: x*y),
    "++": (lambda x: x+1),
    "*2": (lambda x: x*2),
    "mod": (lambda x,y: x % y),
    "/": (lambda x,y: x / y),

    "cons": lambda x,xs: [x] + xs,
    "head": lambda xs: "err-empty-list" if len(xs) == 0 else xs[0],
    "tail": lambda xs: xs[1:],
    "append": lambda x,xs: xs + [x],
    "is-list?": lambda x: isinstance(x, list),

    "compose": lambda f1, f2: lambda x: f1 ( f2 (x)),

    "sleep": time.sleep,
    "help": print_help,
    
    "read": lambda s: parse(input(s)),
    "read-with-macro": lambda s, m: m(parse(input(s))),

    "pwd": os.getcwd(),
    "read-file": read_file,
    "write-file": write_file,
    
    "atom?": lambda x: isinstance(x, (int, str)) # TODO: str può essere stringa o simbolo!
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


def eval_free(ast: List, context: dict, debug=False):
    while True:
        if debug: print(ast)

        if isinstance(ast, (int, float)):
            return ast

        if isinstance(ast, Symbol):
            return context.find(ast)

        if isinstance(ast, list): #bug: e empty list?
            if len(ast) == 0:
                return []

            if ast[0] == "quote":
                return ast[1]

            if ast[0] == "string":
                return ast[1]

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
                context.outermost_add(ast[1], eval_free(ast[2], context)) #funziona per non-ricorsive
                # context.add(ast[1], eval_free(ast[2], context)) #funziona per non-ricorsive
                return ast[1]

            if ast[0] == "cond":
                for clause in ast[1:]:
                    if eval_free(clause[0], context):
                        # breakpoint()
                        ast = clause[1]
                        break
                else:
                    assert eval_free(ast[-1][0], context), f"{ast[-1][0]} should evaluate to T!"
                    print("WARNING")
                    return 

            elif ast[0] == "if":
                if eval_free(ast[1], context):
                    ast = ast[2]
                else:
                    ast = ast[3]

            elif ast[0] == "begin":
                for x in ast[1:-1]:
                    print("EVAL: ", x)
                    eval_free(x, context)
                ast = ast[-1]

            elif ast[0] == "list":
                return [eval_free(el, context) for el in ast[1:]]

            elif ast[0] == "curry":
                ast = ast[1]
                
                num_declared_args = len(ast) - 1

                symbol_eval = eval_free(ast[0], context, debug=debug)
                function_arity = deduce_arity(
                    symbol_eval
                )

                alfabeto = "abcdefghij"
                new_ast = [
                    "lambda",
                    list(alfabeto[:function_arity-num_declared_args]),
                    ast + list(alfabeto[:function_arity-num_declared_args])
                ]
                # breakpoint()
                # print(new_ast)
                return eval_free(
                    new_ast,
                    context,
                    debug=debug
                )
                
            elif ast[0] == "let":   
                # Per esempio, se ho
                # 
                #   (let foo (lambda (x) (if (= x 0) 0 (let-rec (- x 1)))))
                # 
                # Il primo passo è fare EVAL sulla lambda:
                inner_ctx = Context([], [], context)

                MULTI_LET = len(ast) == 3

                if MULTI_LET:
                    for let_clause in ast[1]:

                        let_clause_body = eval_free(let_clause[1], inner_ctx)

                        # Se il corpo del let-rec è effettivamente una procedura (e non
                        # ad es. un numero), essa potrebbe essere ricorsiva.
                        # Per cui, aggiungi nel contesto della procedura
                        # un binding a sé stessa, aka. aggiungi al contesto della procedura
                        # la coppia {foo : Procedure<foo, body=...,>}
                        if isinstance(let_clause_body, Procedure):
                            let_clause_body.ctx.add(let_clause[0], let_clause_body)

                        inner_ctx.add(let_clause[0], let_clause_body)

                else:
                    let_clause_body = eval_free(ast[2], inner_ctx)

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
                if ast[1][0] == "string":
                    ast = eval_free(atom(ast[1][1]), context, debug=debug)
                else:
                    ast = eval_free(ast[1], context, debug=debug)

            elif ast[0] == "print":
                eval_body = eval_free(ast[1], context, debug=debug)
                print(eval_body)
                return eval_body

            else:
                eval_exprs = [eval_free(piece, context, debug=debug) for piece in ast]
                if debug:
                    breakpoint()
                eval_func  = eval_exprs[0]

                if isinstance(eval_func, Procedure):
                    ast = eval_func.body
                    context = Context(eval_func.parms, eval_exprs[1:],
                                      Context(eval_func.ctx.keys(),
                                              eval_func.ctx.values(),
                                              context))
                else:
                    return eval_func(*eval_exprs[1:])


def evalS(program, context=None):
    ast = parse(program)
    if context is None:
        return eval_free(ast, context_base)
    return eval_free(ast, context)


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

assert evalS("()") == []
assert evalS("1") == 1
assert evalS("-1") == -1
assert evalS("(+ 1 2)") == 3
assert evalS("'(3 1 2)") == [3,1,2]
assert evalS(" '(3 1 2)") == [3,1,2]
# assert evalS("(map ++ '(1 2 3))") == [2,3,4]
assert evalS("((compose ++ *2) 1)") == 3
assert evalS("(let ((h (+ 1 2))) (list 1 2 h))") == [1,2,3]

import readline

def ev(program: str, what_to_print=Print.ALL, returns="ctx"):
    user_library = open("lisp/stdlib.lisp", "r").read()
    userctx = eval_program(user_library, what_to_print=what_to_print)
    return eval_program(program, userctx, what_to_print=what_to_print, returns=returns)
    
def repl():
    import traceback
    
    userctx = ev("", what_to_print=Print.FINAL)
    while (inp := input("λ ")) != "q":
        try:
            eval_program(inp, userctx, what_to_print=Print.ALL)
        except Exception:
            print(traceback.format_exc())


def mcirc():
    ev("(metacircular (list if-macro-checker for-macro-sub))")
    
repl()
# mcirc()
