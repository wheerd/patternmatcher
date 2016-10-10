# -*- coding: utf-8 -*-
import unittest

from ddt import data, ddt, unpack

from patternmatcher.constraints import CustomConstraint, MultiConstraint
from patternmatcher.expressions import Operation, Symbol, Variable, Arity, Wildcard, freeze
from patternmatcher.matching import CommutativePatternsParts

f = Operation.new('f', Arity.variadic)
f2 = Operation.new('f2', Arity.variadic)
fc = Operation.new('fc', Arity.variadic, commutative=True)
fc2 = Operation.new('fc2', Arity.variadic, commutative=True)
fa = Operation.new('fa', Arity.variadic, associative=True)
fa2 = Operation.new('fa2', Arity.variadic, associative=True)
fac1 = Operation.new('fac1', Arity.variadic, associative=True, commutative=True)
fac2 = Operation.new('fac2', Arity.variadic, associative=True, commutative=True)
a = Symbol('a')
b = Symbol('b')
c = Symbol('c')
_ = Wildcard.dot()
x_ = Variable.dot('x')
x2 = Variable.fixed('x', 2)
y_ = Variable.dot('y')
z_ = Variable.dot('z')
__ = Wildcard.plus()
x__ = Variable.plus('x')
y__ = Variable.plus('y')
z__ = Variable.plus('z')
___ = Wildcard.star()
x___ = Variable.star('x')
y___ = Variable.star('y')
z___ = Variable.star('z')

constr1 = CustomConstraint(lambda x, y: x == y)
constr2 = CustomConstraint(lambda x, y: x != y)

@ddt
class CommutativePatternsPartsTest(unittest.TestCase):
    @unpack
    @data(
        ([],                          [],             [],             [],                   [],                   []),
        ([a],                         [a],            [],             [],                   [],                   []),
        ([a, b],                      [a, b],         [],             [],                   [],                   []),
        ([x_],                        [],             [],             [],                   [('x', 1)],           []),
        ([x_, y_],                    [],             [],             [],                   [('x', 1), ('y', 1)], []),
        ([x2],                        [],             [],             [],                   [('x', 2)],           []),
        ([f(x_)],                     [],             [f(x_)],        [],                   [],                   []),
        ([f(x_), f(y_)],              [],             [f(x_), f(y_)], [],                   [],                   []),
        ([f(a)],                      [f(a)],         [],             [],                   [],                   []),
        ([f(x__)],                    [],             [],             [],                   [],                   [f(x__)]),
        ([f(a), f(b)],                [f(a), f(b)],   [],             [],                   [],                   []),
        ([x__],                       [],             [],             [('x', 1)],           [],                   []),
        ([x___],                      [],             [],             [('x', 0)],           [],                   []),
        ([x__, y___],                 [],             [],             [('x', 1), ('y', 0)], [],                   []),
        ([fc(x_)],                    [],             [],             [],                   [],                   [fc(x_)]),
        ([fc(x_, a)],                 [],             [],             [],                   [],                   [fc(x_, a)]),
        ([fc(x_, a), fc(x_, b)],      [],             [],             [],                   [],                   [fc(x_, a), fc(x_, b)]),
        ([fc(a)],                     [fc(a)],        [],             [],                   [],                   []),
        ([fc(a), fc(b)],              [fc(a), fc(b)], [],             [],                   [],                   []),
        ([a, x_, x__, f(x_), fc(x_)], [a],            [f(x_)],        [('x', 1)],           [('x', 1)],           [fc(x_)]),
        ([__],                        [],             [],             [(None, 1)],          [],          []),
        ([_],                         [],             [],             [],                   [(None, 1)],          []),
    )
    def test_parts(self, expressions, constant, syntactic, seq_vars, fixed_vars, rest):
        parts = CommutativePatternsParts(None, *map(freeze, expressions))

        self.assertListEqual(constant, sorted(parts.constant))
        self.assertListEqual(syntactic, sorted(parts.syntactic))

        self.assertEqual(len(seq_vars), len(parts.sequence_variables))
        for name, min_count in seq_vars:
            self.assertIn(name, parts.sequence_variables)
            self.assertIn(name, parts.sequence_variable_infos)
            self.assertEqual(min_count, parts.sequence_variable_infos[name].min_count)

        self.assertEqual(len(fixed_vars), len(parts.fixed_variables))
        for name, min_count in fixed_vars:
            self.assertIn(name, parts.fixed_variables)
            self.assertIn(name, parts.fixed_variable_infos)
            self.assertEqual(min_count, parts.fixed_variable_infos[name].min_count)

        self.assertListEqual(rest, sorted(parts.rest))

        self.assertEqual(sum(c for _, c in seq_vars), parts.sequence_variable_min_length)
        self.assertEqual(sum(c for _, c in fixed_vars), parts.fixed_variable_length)

    @unpack
    @data(
        ([None],                      None),
        ([constr1],                   constr1),
        ([constr1, constr1],          constr1),
        ([None, constr1],             constr1),
        ([constr1, None],             constr1),
        ([None, None, constr1],       constr1),
        ([None, constr1, None],       constr1),
        ([constr1, None, None],       constr1),
        ([constr1, constr2],          MultiConstraint({constr1, constr2})),
        ([None, constr1, constr2],    MultiConstraint({constr1, constr2})),
        ([constr1, None, constr2],    MultiConstraint({constr1, constr2})),
        ([constr1, constr2, None],    MultiConstraint({constr1, constr2}))
    )
    def test_fixed_var_constraints(self, constraints, result_constraint):
        parts = CommutativePatternsParts(None, *[Variable('x', Wildcard.dot(), c) for c in constraints])

        self.assertEqual(1, len(parts.fixed_variables.keys()))
        self.assertEqual(len(constraints), len(parts.fixed_variables))
        self.assertIn('x', parts.fixed_variables)
        self.assertIn('x', parts.fixed_variable_infos)

        info = parts.fixed_variable_infos['x']
        self.assertEqual(1, info.min_count)
        self.assertEqual(result_constraint, info.constraint)

    @unpack
    @data(
        ([None],                      None),
        ([constr1],                   constr1),
        ([constr1, constr1],          constr1),
        ([None, constr1],             constr1),
        ([constr1, None],             constr1),
        ([None, None, constr1],       constr1),
        ([None, constr1, None],       constr1),
        ([constr1, None, None],       constr1),
        ([constr1, constr2],          MultiConstraint({constr1, constr2})),
        ([None, constr1, constr2],    MultiConstraint({constr1, constr2})),
        ([constr1, None, constr2],    MultiConstraint({constr1, constr2})),
        ([constr1, constr2, None],    MultiConstraint({constr1, constr2}))
    )
    def test_sequence_var_constraints(self, constraints, result_constraint):
        parts = CommutativePatternsParts(None, *[Variable('x', Wildcard.plus(), c) for c in constraints])

        self.assertEqual(1, len(parts.sequence_variables.keys()))
        self.assertEqual(len(constraints), len(parts.sequence_variables))
        self.assertIn('x', parts.sequence_variables)
        self.assertIn('x', parts.sequence_variable_infos)

        info = parts.sequence_variable_infos['x']
        self.assertEqual(1, info.min_count)
        self.assertEqual(result_constraint, info.constraint)


if __name__ == '__main__':
    unittest.main()