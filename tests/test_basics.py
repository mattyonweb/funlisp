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

    def evto(self, expr: str, obj: Any):
        res = evalS(expr, context=Basics.userctx)
        self.assertEqual(res, obj)
        return res
        
    def compileError(self, expr,
                     exception_types: Union[Exception, Tuple]=None):
        try:
            evalS(expr, context=Basics.userctx)
        except Exception as e:
            if exception_types is None:
                self.assertTrue(True)
                return
            if isinstance(e, exception_types):
                self.assertTrue(True)
                return

            raise e
        
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
