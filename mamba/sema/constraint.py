from enum import Enum


class Constraint(object):

    class Kind(Enum):

        # An equality constraint.
        equals   = 0

        # A conformance constraint.
        #
        # Conformance is a weaker equivalence between two object types T1 T2 stating that T1
        # conforms to T2 if all fields in T2 are contained in T1.
        conforms = 1

        # A specialization constraint.
        #
        # Specialization is an equivalence between two types T1 T2, holding if a particular
        # assignment of the placeholders in T1 makes T1 conform to T2.
        specialize = 2

        # A dusjunction of constraints.
        disjunction = 3

    def __init__(self, kind, source_range=None, **kwargs):
        self.kind = kind
        self.kwargs = kwargs
        self.source_range = source_range
