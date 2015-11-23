# Copyright (c) 2015 VMware, Inc. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#


from oslo_log import log as logging
import pulp
import six

from congress import exception
from functools import reduce

LOG = logging.getLogger(__name__)


class LpLang(object):
    """Represent (mostly) linear programs generated from Datalog."""
    MIN_THRESHOLD = .00001  # for converting <= to <

    class Expression(object):
        def __init__(self, *args, **meta):
            self.args = args
            self.meta = meta

        def __ne__(self, other):
            return not self.__eq__(other)

        def __eq__(self, other):
            if not isinstance(other, LpLang.Expression):
                return False
            if len(self.args) != len(other.args):
                return False
            if self.args[0] in ['AND', 'OR']:
                return set(self.args) == set(other.args)
            comm = ['plus', 'times']
            if self.args[0] == 'ARITH' and self.args[1].lower() in comm:
                return set(self.args) == set(other.args)
            if self.args[0] in ['EQ', 'NOTEQ']:
                return ((self.args[1] == other.args[1] and
                         self.args[2] == other.args[2]) or
                        (self.args[1] == other.args[2] and
                         self.args[2] == other.args[1]))
            return self.args == other.args

        def __str__(self):
            return "(" + ", ".join(str(x) for x in self.args) + ")"

        def __repr__(self):
            args = ", ".join(repr(x) for x in self.args)
            meta = str(self.meta)
            return "<args=%s, meta=%s>" % (args, meta)

        def __hash__(self):
            return hash(tuple([hash(x) for x in self.args]))

        def operator(self):
            return self.args[0]

        def arguments(self):
            return self.args[1:]

        def tuple(self):
            return tuple(self.args)

    @classmethod
    def makeVariable(cls, *args, **meta):
        return cls.Expression("VAR", *args, **meta)

    @classmethod
    def makeBoolVariable(cls, *args, **meta):
        meta['type'] = 'bool'
        return cls.Expression("VAR", *args, **meta)

    @classmethod
    def makeIntVariable(cls, *args, **meta):
        meta['type'] = 'int'
        return cls.Expression("VAR", *args, **meta)

    @classmethod
    def makeOr(cls, *args, **meta):
        if len(args) == 1:
            return args[0]
        return cls.Expression("OR", *args, **meta)

    @classmethod
    def makeAnd(cls, *args, **meta):
        if len(args) == 1:
            return args[0]
        return cls.Expression("AND", *args, **meta)

    @classmethod
    def makeEqual(cls, arg1, arg2, **meta):
        return cls.Expression("EQ", arg1, arg2, **meta)

    @classmethod
    def makeNotEqual(cls, arg1, arg2, **meta):
        return cls.Expression("NOTEQ", arg1, arg2, **meta)

    @classmethod
    def makeArith(cls, *args, **meta):
        return cls.Expression("ARITH", *args, **meta)

    @classmethod
    def makeExpr(cls, obj):
        if isinstance(obj, six.string_types):
            return obj
        if isinstance(obj, (float, six.integer_types)):
            return obj
        op = obj[0].upper()
        if op == 'VAR':
            return cls.makeVariable(*obj[1:])
        if op in ['EQ', 'NOTEQ', 'AND', 'OR']:
            args = [cls.makeExpr(x) for x in obj[1:]]
            if op == 'EQ':
                return cls.makeEqual(*args)
            if op == 'NOTEQ':
                return cls.makeNotEqual(*args)
            if op == 'AND':
                return cls.makeAnd(*args)
            if op == 'OR':
                return cls.makeOr(*args)
            raise cls.LpConversionFailure('should never happen')
        args = [cls.makeExpr(x) for x in obj[1:]]
        return cls.makeArith(obj[0], *args)

    @classmethod
    def isConstant(cls, thing):
        return (isinstance(thing, six.string_types) or
                isinstance(thing, (float, six.integer_types)))

    @classmethod
    def isVariable(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'VAR'

    @classmethod
    def isEqual(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'EQ'

    @classmethod
    def isOr(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'OR'

    @classmethod
    def isAnd(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'AND'

    @classmethod
    def isNotEqual(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'NOTEQ'

    @classmethod
    def isArith(cls, thing):
        return isinstance(thing, cls.Expression) and thing.args[0] == 'ARITH'

    @classmethod
    def isBoolArith(cls, thing):
        return (cls.isArith(thing) and
                thing.args[1].lower() in ['lteq', 'lt', 'gteq', 'gt', 'equal'])

    @classmethod
    def variables(cls, exp):
        if cls.isConstant(exp):
            return set()
        elif cls.isVariable(exp):
            return set([exp])
        else:
            variables = set()
            for arg in exp.arguments():
                variables |= cls.variables(arg)
            return variables

    def __init__(self):
        # instance variable so tests can be run in parallel
        self.fresh_var_counter = 0   # for creating new variables

    def pure_lp(self, exp, bounds):
        """Rewrite EXP to a pure LP problem.

        :param exp is an Expression of the form
        var = (arith11 ^ ... ^ arith1n) | ... | (arithk1 ^ ... ^ arithkn)
        where the degenerate cases are permitted as well.

        Returns a collection of expressions each of the form:
        a1*x1 + ... + an*xn [<=, ==, >=] b.
        """
        flat, support = self.flatten(exp, indicator=False)
        flats = support
        flats.append(flat)
        result = []
        for flat in flats:
            # LOG.info("flat: %s", flat)
            no_and_or = self.remove_and_or(flat)
            # LOG.info("   without and/or: %s", no_and_or)
            no_indicator = self.indicator_to_pure_lp(no_and_or, bounds)
            # LOG.info("   without indicator: %s",
            #          ";".join(str(x) for x in no_indicator))
            result.extend(no_indicator)
        return result

    def pure_lp_term(self, exp, bounds):
        """Rewrite term exp to a pure LP term.

        :param exp is an Expression of the form
        (arith11 ^ ... ^ arith1n) | ... | (arithk1 ^ ... ^ arithkn)
        where the degenerate cases are permitted as well.

        Returns (new-exp, support) where new-exp is a term, and support is
        a expressions of the following form.
        a1*x1 + ... + an*xn [<=, ==, >=] b.
        """
        flat, support = self.flatten(exp, indicator=False)
        flat_no_andor = self.remove_and_or_term(flat)
        results = []
        for s in support:
            results.extend(self.pure_lp(s, bounds))
        return flat_no_andor, results

    def remove_and_or(self, exp):
        """Translate and/or operators into times/plus arithmetic.

        :param exp is an Expression that takes one of the following forms.
        var [!]= term1 ^ ... ^ termn
        var [!]= term1 | ... | termn
        var [!]= term1
        where termi is an indicator variable.

        Returns an expression equivalent to exp but without any ands/ors.
        """
        if self.isConstant(exp) or self.isVariable(exp):
            return exp
        op = exp.operator().lower()
        if op in ['and', 'or']:
            return self.remove_and_or_term(exp)
        newargs = [self.remove_and_or(arg) for arg in exp.arguments()]
        constructor = self.operator_to_constructor(exp.operator())
        return constructor(*newargs)

    def remove_and_or_term(self, exp):
        if exp.operator().lower() == 'and':
            op = 'times'
        else:
            op = 'plus'
        return self.makeArith(op, *exp.arguments())

    def indicator_to_pure_lp(self, exp, bounds):
        """Translate exp into LP constraints without indicator variable.

        :param exp is an Expression of the form var = arith
        :param bounds is a dictionary from variable to its upper bound

        Returns [EXP] if it is of the wrong form. Otherwise, translates
        into the form y = x < 0, and then returns two constraints where
        upper(x) is the upper bound of the expression x:
            -x <= y * upper(x)
            x < (1 - y) * upper(x)
        Taken from section 7.4 of
        http://www.aimms.com/aimms/download/manuals/
        aimms3om_integerprogrammingtricks.pdf
         """
        # return exp unchanged if exp not of the form <var> = <arith>
        #   and figure out whether it's <var> = <arith> or <arith> = <var>
        if (self.isConstant(exp) or self.isVariable(exp) or
                not self.isEqual(exp)):
            return [exp]
        args = exp.arguments()

        lhs = args[0]
        rhs = args[1]
        if self.isVariable(lhs) and self.isArith(rhs):
            var = lhs
            arith = rhs
        elif self.isVariable(rhs) and self.isArith(lhs):
            var = rhs
            arith = lhs
        else:
            return [exp]
        # if arithmetic side is not an inequality, not an indicator var
        if not self.isBoolArith(arith):
            return [exp]

        # Do the transformation.
        x = self.arith_to_lt_zero(arith).arguments()[1]
        y = var
        LOG.info("   x: %s", x)
        upper_x = self.upper_bound(x, bounds) + 1
        LOG.info("   bounds(x): %s", upper_x)
        # -x <= y * upper(x)
        c1 = self.makeArith(
            'lteq',
            self.makeArith('times', -1, x),
            self.makeArith('times', y, upper_x))
        # x < (1 - y) * upper(x)
        c2 = self.makeArith(
            'lt',
            x,
            self.makeArith('times', self.makeArith('minus', 1, y), upper_x))
        return [c1, c2]

    def arith_to_lt_zero(self, expr):
        """Returns Arith expression equivalent to expr but of the form A < 0.

        :param expr is an Expression
        Returns an expression equivalent to expr but of the form A < 0.
        """
        if not self.isArith(expr):
            raise self.LpConversionFailure(
                "arith_to_lt_zero takes Arith expr but received %s", expr)
        args = expr.arguments()
        op = args[0].lower()
        lhs = args[1]
        rhs = args[2]
        if op == 'lt':
            return LpLang.makeArith(
                'lt', LpLang.makeArith('minus', lhs, rhs), 0)
        elif op == 'lteq':
            return LpLang.makeArith(
                'lt',
                LpLang.makeArith(
                    'minus',
                    LpLang.makeArith('minus', lhs, rhs),
                    self.MIN_THRESHOLD),
                0)
        elif op == 'gt':
            return LpLang.makeArith(
                'lt', LpLang.makeArith('minus', rhs, lhs), 0)
        elif op == 'gteq':
            return LpLang.makeArith(
                'lt',
                LpLang.makeArith(
                    'minus',
                    LpLang.makeArith('minus', rhs, lhs),
                    self.MIN_THRESHOLD),
                0)
        else:
            raise self.LpConversionFailure(
                "unhandled operator %s in %s" % (op, expr))

    def upper_bound(self, expr, bounds):
        """Returns number giving an upper bound on the given expr.

        :param expr is an Expression
        :param bounds is a dictionary from tuple versions of variables
        to the size of their upper bound.
        """
        if self.isConstant(expr):
            return expr
        if self.isVariable(expr):
            t = expr.tuple()
            if t not in bounds:
                raise self.LpConversionFailure("not bound given for %s" % expr)
            return bounds[expr.tuple()]
        if not self.isArith(expr):
            raise self.LpConversionFailure(
                "expression has no bound: %s" % expr)
        args = expr.arguments()
        op = args[0].lower()
        exps = args[1:]
        if op == 'times':
            f = lambda x, y: x * y
            return reduce(f, [self.upper_bound(x, bounds) for x in exps], 1)
        if op == 'plus':
            f = lambda x, y: x + y
            return reduce(f, [self.upper_bound(x, bounds) for x in exps], 0)
        if op == 'minus':
            return self.upper_bound(exps[0], bounds)
        if op == 'div':
            raise self.LpConversionFailure("No bound on division %s" % expr)
        raise self.LpConversionFailure("Unknown operator for bound: %s" % expr)

    def flatten(self, exp, indicator=True):
        """Remove toplevel embedded and/ors by creating new equalities.

        :param exp is an Expression of the form
        var = (arith11 ^ ... ^ arith1n) | ... | (arithk1 ^ ... ^ arithkn)
        where arithij is either a variable or an arithmetic expression
        where the degenerate cases are permitted as well.

        :param indicator controls whether the method Returns
        a single variable (with supporting expressions) or it Returns
        an expression that has operator with (flat) arguments

        Returns a collection of expressions each of one of the following
        forms:
        var1 = var2 * ... * varn
        var1 = var2 + ... + varn
        var1 = arith

        Returns (new-expression, supporting-expressions)
        """
        if self.isConstant(exp) or self.isVariable(exp):
            return exp, []
        new_args = []
        extras = []
        new_indicator = not (exp.operator().lower() in ['eq', 'noteq'])
        for e in exp.arguments():
            newe, extra = self.flatten(e, indicator=new_indicator)
            new_args.append(newe)
            extras.extend(extra)
        constructor = self.operator_to_constructor(exp.operator())
        new_exp = constructor(*new_args)
        if indicator:
            indic, extra = self.create_intermediate(new_exp)
            return indic, extra + extras
        return new_exp, extras

    def operator_to_constructor(self, operator):
        """Given the operator, return the corresponding constructor."""
        op = operator.lower()
        if op == 'eq':
            return self.makeEqual
        if op == 'noteq':
            return self.makeNotEqual
        if op == 'var':
            return self.makeVariable
        if op == 'and':
            return self.makeAnd
        if op == 'or':
            return self.makeOr
        if op == 'arith':
            return self.makeArith
        raise self.LpConversionFailure("Unknown operator: %s" % operator)

    def create_intermediate(self, exp):
        """Given expression, create var = expr and return (var, var=expr)."""
        if self.isBoolArith(exp) or self.isAnd(exp) or self.isOr(exp):
            var = self.freshVar(type='bool')
        else:
            var = self.freshVar()
        equality = self.makeEqual(var, exp)
        return var, [equality]

    def freshVar(self, **meta):
        var = self.makeVariable('internal', self.fresh_var_counter, **meta)
        self.fresh_var_counter += 1
        return var

    class LpConversionFailure(exception.CongressException):
        pass


class PulpLpLang(LpLang):
    """Algorithms for translating LpLang into PuLP library problems."""
    MIN_THRESHOLD = .00001

    def __init__(self):
        # instance variable so tests can be run in parallel
        super(PulpLpLang, self).__init__()
        self.value_counter = 0

    def problem(self, optimization, constraints, bounds):
        """Return PuLP problem for given optimization and constraints.

        :param optimization is an LpLang.Expression that is either a sum
            or product to minimize.
        :param constraints is a collection of LpLang.Expression that
            each evaluate to true/false (typically equalities)
        :param bounds is a dictionary mapping LpLang.Expression variable
            tuples to their upper bounds.

        Returns a pulp.LpProblem.
        """
        # translate constraints to pure LP
        optimization, hard = self.pure_lp_term(optimization, bounds)
        for c in constraints:
            hard.extend(self.pure_lp(c, bounds))
        LOG.info("* Converted DatalogLP to PureLP *")
        LOG.info("optimization: %s", optimization)
        LOG.info("constraints: \n%s", "\n".join(str(x) for x in hard))

        # translate optimization and constraints into PuLP equivalents
        variables = {}
        values = {}
        optimization = self.pulpify(optimization, variables, values)
        hard = [self.pulpify(c, variables, values) for c in hard]

        # add them to the problem.
        prob = pulp.LpProblem("VM re-assignment", pulp.LpMinimize)
        prob += optimization
        for c in hard:
            prob += c

        # invert values
        return prob, {value: key for key, value in values.items()}

    def pulpify(self, expr, variables, values):
        """Return PuLP version of expr.

        :param expr is an Expression of one of the following forms.
        arith
        arith = arith
        arith <= arith
        arith >= arith
        :param vars is a dictionary from Expression variables to PuLP variables

        Returns a PuLP representation of expr.
        """
        # LOG.info("pulpify(%s, %s)", expr, variables)
        if self.isConstant(expr):
            return expr
        elif self.isVariable(expr):
            return self._pulpify_variable(expr, variables, values)
        elif self.isArith(expr):
            args = expr.arguments()
            op = args[0]
            args = [self.pulpify(arg, variables, values) for arg in args[1:]]
            if op == 'times':
                return reduce(lambda x, y: x * y, args)
            elif op == 'plus':
                return reduce(lambda x, y: x + y, args)
            elif op == 'div':
                return reduce(lambda x, y: x / y, args)
            elif op == 'minus':
                return reduce(lambda x, y: x - y, args)
            elif op == 'lteq':
                return (args[0] <= args[1])
            elif op == 'gteq':
                return (args[0] >= args[1])
            elif op == 'gt':  # pulp makes MIN_THRESHOLD 1
                return (args[0] >= args[1] + self.MIN_THRESHOLD)
            elif op == 'lt':  # pulp makes MIN_THRESHOLD 1
                return (args[0] + self.MIN_THRESHOLD <= args[1])
            else:
                raise self.LpConversionFailure(
                    "Found unsupported operator %s in %s" % (op, expr))
        else:
            args = [self.pulpify(arg, variables, values)
                    for arg in expr.arguments()]
            op = expr.operator().lower()
            if op == 'eq':
                return (args[0] == args[1])
            elif op == 'noteq':
                return (args[0] != args[1])
            else:
                raise self.LpConversionFailure(
                    "Found unsupported operator: %s" % expr)

    def _new_value(self, old, values):
        """Create a new value for old and store values[old] = new."""
        if old in values:
            return values[old]
        new = self.value_counter
        self.value_counter += 1
        values[old] = new
        return new

    def _pulpify_variable(self, expr, variables, values):
        """Translate DatalogLp variable expr into PuLP variable.

        :param expr is an instance of Expression
        :param variables is a dictionary from Expressions to pulp variables
        :param values is a 1-1 dictionary from strings/floats to integers
               representing a mapping of non-integer arguments to variable
               names to their integer equivalents.
        """
        # pulp mangles variable names that contain certain characters.
        # Replace actual args with integers when constructing
        #   variable names.  Includes integers since we don't want to
        #   have namespace collision problems.
        oldargs = expr.arguments()
        args = [oldargs[0]]
        for arg in oldargs[1:]:
            newarg = self._new_value(arg, values)
            args.append(newarg)
        # name
        name = "_".join([str(x) for x in args])
        # type
        typ = expr.meta.get('type', None)
        if typ == 'bool':
            cat = pulp.LpBinary
        elif typ == 'int':
            cat = pulp.LpInteger
        else:
            cat = pulp.LpContinuous
        # set bounds
        lowbound = expr.meta.get('lowbound', None)
        upbound = expr.meta.get('upbound', None)
        var = pulp.LpVariable(
            name=name, cat=cat, lowBound=lowbound, upBound=upbound)

        # merge with existing variable, if any
        if expr in variables:
            newvar = self._resolve_var_conflicts(variables[expr], var)
            oldvar = variables[expr]
            oldvar.cat = newvar.cat
            oldvar.lowBound = newvar.lowBound
            oldvar.upBound = newvar.upBound
        else:
            variables[expr] = var
        return variables[expr]

    def _resolve_var_conflicts(self, var1, var2):
        """Returns variable that combines information from var1 and var2.

        :param meta1 is a pulp.LpVariable
        :param meta2 is a pulp.LpVariable

        Returns new pulp.LpVariable representing the conjunction of constraints
        from var1 and var2.
        Raises LpConversionFailure if the names of var1 and var2 differ.
        """

        def type_lessthan(x, y):
            return ((x == pulp.LpBinary and y == pulp.LpInteger) or
                    (x == pulp.LpBinary and y == pulp.LpContinuous) or
                    (x == pulp.LpInteger and y == pulp.LpContinuous))

        if var1.name != var2.name:
            raise self.LpConversionFailure(
                "Can't resolve variable name conflict: %s and %s" % (
                    var1, var2))
        name = var1.name
        if type_lessthan(var1.cat, var2.cat):
            cat = var1.cat
        else:
            cat = var2.cat
        if var1.lowBound is None:
            lowbound = var2.lowBound
        elif var2.lowBound is None:
            lowbound = var1.lowBound
        else:
            lowbound = max(var1.lowBound, var2.lowBound)
        if var1.upBound is None:
            upbound = var2.upBound
        elif var2.upBound is None:
            upbound = var1.upBound
        else:
            upbound = min(var1.upBound, var2.upBound)
        return pulp.LpVariable(
            name=name, lowBound=lowbound, upBound=upbound, cat=cat)
