from copy import copy

from .constraint import Constraint
from . import exc
from . import types


class ConstraintSolver(object):

    def __init__(self, constraints, partial_solution=None):
        self.constraints = constraints
        self.solution = partial_solution or {}

        self.done = False
        self.sub_systems = []

    def __iter__(self):
        return self.solutions()

    def solutions(self):
        # Solve as many constraints as possible before transfering control to a sub-system.
        while self.constraints:
            try:
                self.solve_constraint(self.constraints.pop())
            except exc.SemanticError as error:
                yield error
                return

        # If there are no sub-system to solve, yield the current solution and stops the iteration.
        if not self.sub_systems:
            # TODO: Reify the results
            yield self.solution
            return

        # Otherwise iterate through all sub-sustems.
        while self.sub_systems:
            sub_system = self.sub_systems.pop()
            for result in sub_system:
                yield result

    def solve_constraint(self, constraint):
        if constraint.kind == Constraint.Kind.equals:
            self.solve_equality(constraint)
        elif constraint.kind == Constraint.Kind.conforms:
            self.solve_conformity(constraint)
        elif constraint.kind == Constraint.Kind.specializes:
            self.solve_specialization(constraint)
        elif constraint.kind == Constraint.Kind.disjunction:
            self.sub_systems = [
                ConstraintSolver(
                    constraints=[choice] + self.constraints,
                    partial_solution=copy(self.solution))
                for choice in constraint.choices
            ]
            self.constraints = []
        else:
            assert False, f"unexpected constraint kind: '{constraint.kind}'"

    def solve_equality(self, constraint):
        self.unify(constraint.lhs, constraint.rhs, constraint.source_range)

    def solve_conformity(self, constraint):
        # FIXME
        self.unify(constraint.lhs, constraint.rhs, constraint.source_range)

    def solve_specialization(self, constraint):
        # FIXME
        self.unify(constraint.lhs, constraint.rhs, constraint.source_range)

    def unify(self, ty0, ty1, source_range, memo=None):
        """
        Unifies two types.

        Unification is the mechanism we use to bind type variables to their actual type. The main
        concept is that given two types (possibly aggregates of multiple subtypes), we try to find
        one possible binding for which the types are equivalent. If such binding can't be found,
        then the constraints are unsatisfiable, meaning that the program is type-inconsistent.
        """
        memo = memo if memo is not None else {}

        a = self.walk(ty0)
        b = self.walk(ty1)

        # Nothing to unify if the types are already equal.
        if a is b:
            return

        # If one of the types is a variable, unify it with the other.
        if isinstance(a, types.TypeVariable):
            self.solution[a] = b
            return
        if isinstance(b, types.TypeVariable):
            self.solution[b] = a
            return

        # If both types are function ...
        if isinstance(a, types.FunctionType) and isinstance(b, types.FunctionType):
            # Check for domain lenghts.
            if len(a.domain) != len(b.domain):
                raise exc.UnificationError(a, b, 'different domain lenghts', source_range)

            # Unify domains and codomain.
            self.unify(a.domain, b.domain, source_range, memo=memo)
            self.unify(a.codomain, b.codomain, source_range, memo=memo)
            return

        # If both types are object types ...
        if isinstance(a, types.ObjectType) and isinstance(b, types.ObjectType):
            # Take into account the possible use of the syntactic sugar that consists of omitting
            # property labels when there's only one.
            if (
                (len(a) == 1) and ('_0' in a.properties) or
                (len(b) == 1) and ('_0' in b.properties)
            ):
                _, lhs = next(iter(a.properties.items()))
                _, rhs = next(iter(b.properties.items()))
                self.unify(lhs, rhs, source_range, memo=memo)
            else:
                for prop_name in a:
                    if prop_name not in b:
                        raise exc.UnificationError(a, b, 'incompatible types', source_range)
                    self.unify(a[prop_name], b[prop_name], source_range, memo=memo)
            return

        raise exc.UnificationError(a, b, 'incompatible types', source_range)

    def walk(self, ty):
        if not isinstance(ty, types.TypeVariable):
            return ty
        if ty in self.solution:
            return self.walk(self.solution[ty])
        return ty
