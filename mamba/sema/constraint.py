from enum import Enum


class Constraint(object):

    class Kind(Enum):

        # An equality constraint.
        equals = 1

        # A specialization constraint.
        #
        # Specialization is an equivalence between two types T1 T2, holding if a particular
        # assignment of the placeholders in T1 makes T1 conform to T2.
        specializes = 2

        # A conformance constraint.
        #
        # Conformance is a weaker equivalence between two object types T1 T2 stating that T1
        # conforms to T2 if all fields in T2 are contained in T1.
        conforms = 3

        # A dusjunction of constraints.
        disjunction = 4

    def __init__(self, kind, source_range=None, **kwargs):
        self.kind = kind
        self.kwargs = kwargs
        self.source_range = source_range

    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return self.kwargs[attr]

    def __lt__(self, other):
        return self.kind.value < other.kind.value

    def __repr__(self):
        loc = str(self.source_range.start)
        if self.kind == Constraint.Kind.disjunction:
            choices = '\n'.join('  ' + repr(c) for c in self.choices)
            return f"{loc:6s}:\n{choices}"

        if self.kind == Constraint.Kind.equals:
            return f"{loc:6s}: '{self.lhs}' = '{self.rhs}'"
        if self.kind == Constraint.Kind.conforms:
            return f"{loc:6s}: '{self.lhs}' ⊂ '{self.rhs}'"
        if self.kind == Constraint.Kind.specializes:
            return f"{loc:6s}: '{self.lhs}' ⊨ '{self.rhs}'"
        return object.__repr__(self)
