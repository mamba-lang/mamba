from mamba import ast

from .constraint import Constraint
from . import exc
from . import types


class ConstraintInferer(ast.Visitor):
    """Static analysis pass that infers the types of all nodes in the AST."""

    def __init__(self):
        self.errors = []
        self.constraints = []

    def visit_TypeDeclaration(self, node):
        # Skip this node if its symbol wasn't been created due to a problem during symbol binding.
        if node.symbol is None:
            return

        # Create the declared type.
        node.type = create_type(node.body)
        if node.placeholders:
            if isinstance(node.type, types.UnionType):
                for ty in node.type:
                    ty.placeholders = node.placeholders
            else:
                node.type.placeholders = node.placeholders

        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals, lhs=node.symbol.type, rhs=node.type,
            source_range=node.source_range))

    def visit_FunctionDeclaration(self, node):
        # Skip this node if its symbol wasn't been created due to a problem during symbol binding.
        if node.symbol is None:
            return

        # Create the type of the declared function.
        domain = create_type(node.domain)
        codomain = create_type(node.codomain)
        node.type = types.FunctionType(domain, codomain, node.placeholders)

        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals, lhs=node.symbol.type, rhs=node.type,
            source_range=node.source_range))

        self.visit(node.body)

    def visit_Identifier(self, node):
        # Skip this node if its scope wasn't been created due to a problem during symbol binding.
        if (node.scope is None):
            return
        symbols = node.scope[node.name]
        if not symbols:
            return

        # Get all symbols the identifier might be eventually bound to.
        symbols = node.scope[node.name]
        # Process the generic specializers (if any).
        args = { name: create_type(ty) for name, type in (node.specializers or {}) }

        # Create equality and specialization constraints.
        node.type = types.TypeVariable()
        for symbol in symbols:
            if args:
                self.constraints.append(Constraint(
                    kind=Constraint.Kind.specialize,
                    lhs=node.type,
                    rhs=symbol.type,
                    args=args))
            else:
                self.constraints.append(Constraint(
                    kind=Constraint.Kind.equals,
                    lhs=node.type,
                    rhs=symbol.type))


def create_type(node):
    if isinstance(node, ast.UnionType):
        return types.UnionType([create_type(t) for t in node.types])

    if isinstance(node, ast.ObjectType):
        properties = {}
        for prop in node.properties:
            assert isinstance(prop, ast.ObjectProperty)
            if prop.name in properties:
                raise exc.DuplicateDeclaration(name=prop.name, source_range=prop.source_range)
            elif prop.annotation is None:
                properties[prop.name] = types.TypeVariable()
            else:
                properties[prop.name] = create_type(prop.annotation)

        return types.ObjectType(properties=properties)

    if isinstance(node, ast.Identifier):
        # Make sure the symbol is bound and not overloaded.
        if node.scope is None:
            raise exc.UnboundName(name=node.name, source_range=node.source_range)
        symbols = node.scope[node.name]
        if not symbols:
            raise exc.UnboundName(name=node.name, source_range=node.source_range)
        if len(symbols) > 1:
            raise exc.SemanticError(
                message=f"'{node.name}' is overloaded", source_range=node.source_range)
        symbol = symbols[0]

        # Since we don't allow dynamic typing, the symbol of an type identifier should be either a
        # type alias, or a type placeholder.
        if isinstance(symbol.type, types.TypeAlias):
            node.type = symbol.type.subject
            return node.type
        if isinstance(symbol.type, types.TypePlaceholder):
            node.type = symbol.type
            return node.type

    raise exc.SemanticError(message=f"'{node}' is not a type", source_range=node.source_range)
