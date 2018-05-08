from copy import copy
from functools import reduce

from .constraint import Constraint
from . import exc
from . import types


class ConstraintSolver(object):

    def __init__(self, constraints, partial_solution=None):
        self.constraints = sorted(constraints)
        self.solution = partial_solution or {}

        self.done = False
        self.sub_systems = []

    def __iter__(self):
        return self.solutions()

    def solutions(self):
        # Solve as many constraints as possible before transfering control to a sub-system.
        h = None
        while self.constraints:
            # Make sure the computation's not stuck.
            new_h = reduce(lambda a, b: a ^ b, map(id, self.constraints))
            if new_h == h:
                raise exc.SemanticError('constraint system appear to be unsolvable')
            h = new_h

            try:
                self.solve_constraint(self.constraints.pop(0))
            except exc.SemanticError as error:
                yield error
                return

        # If there are no sub-system to solve, yield the current solution and stops the iteration.
        if not self.sub_systems:
            yield {
                var: self.deep_walk(ty)
                for var, ty in self.solution.items()
            }
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
        a = self.walk(constraint.lhs)
        b = self.walk(constraint.rhs)

        # Defer the constraint if the unspecialized type is yet unknown.
        if isinstance(b, types.TypeVariable):
            self.constraints.append(constraint)
            return

        # If the unspecialized type isn't generic, this boils down to an equality constraint.
        if not getattr(b, 'placeholders', None):
            self.solve_equality(constraint)
            return

        # Make sure no undefined specialization argument was supplied.
        unspecified = set(constraint.args) - set(b.placeholders)
        if unspecified:
            raise exc.SemanticError(
                source_range=constraint.source_range,
                message=f'superfluous explicit specializations: {unspecified}')

        # Specialize the type on the left so that it matches that on the right.
        specialized = specialize(generic=b, pattern=a)
        self.solve_equality(Constraint(
            kind=Constraint.Kind.equals,
            lhs=specialized,
            rhs=a,
            source_range=constraint.source_range))

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
                        (a, b) = (self.deep_walk(a), self.deep_walk(b))
                        raise exc.UnificationError(a, b, 'incompatible types', source_range)
                    self.unify(a[prop_name], b[prop_name], source_range, memo=memo)
            return

        (a, b) = (self.deep_walk(a), self.deep_walk(b))
        raise exc.UnificationError(a, b, 'incompatible types', source_range)

    def walk(self, ty):
        if not isinstance(ty, types.TypeVariable):
            return ty
        if ty in self.solution:
            return self.walk(self.solution[ty])
        return ty

    def deep_walk(self, ty, memo=None):
        memo = memo if memo is not None else {}

        if isinstance(ty, types.TypeVariable):
            walked = self.walk(ty)
            if not isinstance(walked, types.TypeVariable):
                return self.deep_walk(walked, memo=memo)
            return walked

        if isinstance(ty, types.TypeAlias):
            return types.TypeAlias(subject=self.deep_walk(ty.subject, memo=memo))

        if isinstance(ty, types.FunctionType):
            return types.FunctionType(
                domain=self.deep_walk(ty.domain, memo=memo),
                codomain=self.deep_walk(ty.codomain, memo=memo),
                placeholders=ty.placeholders)

        if isinstance(ty, types.ObjectType):
            if ty in memo:
                return memo[ty]
            walked = types.ObjectType(placeholders=ty.placeholders)
            memo[ty] = walked

            for key, value in ty.properties.items():
                walked.properties[key] = self.deep_walk(value, memo=memo)
            return walked

        if isinstance(ty, types.Type):
            return ty

        assert False, f"unexpected type f'{type(ty)}'"


class SpecializationError(Exception):
    pass


def specialize(generic, pattern, memo=None):
    # Nothing to do if the generic type and the pattern are already equivalent.
    if generic is pattern:
        return generic

    # Avoid infinite recursions.
    memo = memo if memo is not None else {}
    if generic in memo:
        return memo[generic]

    # If the generic type is a placeholder, use the pattern if possible.
    if isinstance(generic, types.TypePlaceholder):
        # Make sure the generic type is compatible with the given pattern, for every occurence of a
        # given type placeholder.
        if (generic in memo) and not (pattern == memo[generic]):
            raise SpecializationError()
        memo[generic] = pattern
        return pattern

    # If the generic type or the specialization pattern is a variable, return it.
    if isinstance(generic, types.TypeVariable) or isinstance(pattern, types.TypeVariable):
        return generic

    if isinstance(generic, types.FunctionType) and isinstance(pattern, types.FunctionType):
        domain = specialize(generic.domain, pattern.domain, memo=memo)
        codomain = specialize(generic.codomain, pattern.codomain, memo=memo)
        return types.FunctionType(domain=domain, codomain=codomain)

    assert False
