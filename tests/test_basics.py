import unittest
from lisp.compiler import *
from lisp.utils import *
import random

class Basics(unittest.TestCase):
    with open("lisp/stdlib.lisp", "r") as f:
        userctx = eval_program(
            f.read(),
            what_to_print=Print.NOTHING
        )

    def eval(self, expr: str, debug=False):
        return evalS(expr, context=Basics.userctx, debug=debug)

    
    def evto(self, expr: str, obj: Any, debug=False, note:str=None):
        res = self.eval(expr, debug=debug)
        self.assertEqual(res, obj)

        if note:
            print()
            print(f"{expr}  = {res}")
            print(f"Explanation: {note}")            

        return res

    
    def compileError(self, expr,
                     exception_types: Union[Exception, Tuple]=None,
                     note:str=None):
        try:
            evalS(expr, context=Basics.userctx)
        except Exception as e:
            if exception_types is None:
                self.assertTrue(True)
            elif isinstance(e, exception_types):
                self.assertTrue(True)
            else:
                raise e

            if note is not None:
                print()
                print(f"{expr} raises {e}")
                print(f"Explanation: {note}")
        
    def test_no_expressions(self):
        self.evto("()", [])
        self.evto("1", 1)
        self.evto("-1", -1)

    def test_aritmethic_expressions(self):
        self.evto("(+ 1 2)", 3)
        self.evto("(+ -1 2)", 1)
        self.evto("(+ (- 1 10) 2)", -7)
        self.evto("(* 2 (- 1 10))", -18)
        self.evto("(* -2 (- 1 10))", +18)

    def test_wrong_parser(self):
        pass #TODO

    def test_empty_lists(self):
        self.evto("()", [])
        self.evto("'()", [])
        self.evto("(list)", [])

    def test_nested_empty_lists(self):
        # The best way to write nested empty lists
        self.evto("(list (list))", [[]])
        self.evto("(list (list (list)))", [[[]]])

        # () would be considered as a function name!
        self.compileError("(())", TypeError)

        # `list` would be interpreted as a symbol
        # self.compileError("list", TypeError)
        
        self.evto("'(())", [[]])
        self.evto("'('())", [["quote", []]])

        
    def test_simple_lists(self):
        self.evto("'(1)", [1])
        self.evto("(list 1)", [1])

        self.evto("'(3 1 2)", [3,1,2])
        self.evto("(list 3 1 2)", [3,1,2])

        
    def test_nested_lists(self):
        # Whenever you deal with nested list, use `(list <...>)`.
        # Notation '(<...>) will not work because /EVERYTHING/ inside
        # parenthesis will be quoted!
        self.evto("(list 3 '(1 5) 2)", [3,[1,5],2])

        # Most external quote will... quote everything internal
        self.evto("'(3 '(1 5) 2)", [3, ["quote", [1,5]],2])

        # More nested
        self.evto("(list 3 (list 1 (list 5 4)) 2)",
                  [3, [1, [5,4]], 2])

        # Notation '(elem1 elem2 ...) is not the best idea, as elements
        # inside the list are not evaluated
        self.evto("'(1 '(2 3) 4)",
                  [1, ["quote", [2, 3]], 4])

        # Even more so, another example of why avoid quote notation for lists
        self.evto("'(1 (+ 2 3) 4)",
                  [1, ["+", 2, 3], 4])


    def test_equiv_quote_list(self):
        # For plain lists, '(1 2 3) and (list 1 2 3) are equal.
        import random
        
        for _ in range(50):
            l = [random.randint(-10, 10) for _ in range(random.randint(0, 11))]
            numbers = " ".join([str(n) for n in l])

            self.evto(f"(list {numbers})", l)
            self.evto(f"'({numbers})", l)

            
    def test_higher_order_funcs_list(self):
        self.evto("(map ++ (list 1 2 3))", [2,3,4])
        self.evto(
            "(map (lambda (x) (map ++ x)) (list (list 1) (list 2 4) (list 3)))",
            [[2], [3,5], [4]]
        )
        
        
    def test_basic_currying(self):
        self.evto(
            "(map (curry (map ++)) (list (list 1) (list 2)))",
            [[2],[3]]
        )

        # pseudo-python: `compose(lambda x:x+1)(lambda x:x*100)(1) = 101`
        # Composition compose as always from right to left
        self.evto("(((curry (compose ++)) (lambda (x) (* x 100))) 1)", 101)

    def test_simple_eval(self):
        self.evto("(eval '())", [])
        self.evto("(eval 1)", 1)

        self.compileError(
            "(eval (list 1 2 3))", TypeError,
            "The expression (1 2 3) reads 1 as a function!"
        )
        self.compileError(
            "(eval '(1 2 3))", TypeError,
            "The expression (1 2 3) reads 1 as a function!"
        )
        
        self.evto("(eval (list 1 2 3))", [1,2,3])

        # (eval (quote X)) = X
        # Attenzione: diverso da dire (eval (quote X)) = (eval X)!
        self.evto("(eval '(list 1 2 3))", ["list", 1,2,3])
        self.evto("(eval (quote (list 1 2 3)))", ["list", 1,2,3])

        self.evto("(eval (list 1 (+ 1 2) 4))", [1,3,4])
        self.evto("(eval '(list 1 (+ 1 2) 4))", ["list", 1, ["+", 1, 2], 4])

        
    def test_evalS(self):
        self.evto("""(+ (evalS "(+ 99 1)") 1)""", 101)
        self.evto("""(+ (evalS (read-file "tests/sample.file")) 1)""", 21)

        # TODO: PBT
        self.evto(
            """(evalS "(eval '(list 1 2 3))")""",
            self.eval("(eval '(list 1 2 3))")
        )

        
    def test_simple_let(self):
        self.evto("(let x 0 (+ x 1))", 1, note="Single let")

        # Multiple-let 
        self.evto("(let ((x 0) (y 1)) (+ x y))", 1, note="Multiple let")

        self.evto("(let ((h (+ 1 2))) (list 1 2 h))", [1,2,3])

        self.evto("(let ((h 1) (x (+ h 1))) x)", 2, note="Mutually binding let")

        
    def test_recursive_let(self):
        self.evto(
            "(let foo (lambda (x) (if (< x 0) 0 (foo (- x 1)))) (foo 5))",
            0
        )        

