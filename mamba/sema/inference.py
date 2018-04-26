from mamba import ast

from .constraint import Constraint
from . import exc
from . import types


class TypeBuilder(ast.Visitor):
    """
    The static analysis pass that creates processes type declarations.

    The goal of this pass is to create the types described by type definitions, and to associate
    them with their corresponding symbol. This is the first step of type inference.
    """

    def __init__(self):
        self.errors = []
        self.constraints = []

    def visit_TypeDeclaration(self, node):
        # Skip this node if its symbol wasn't been created, which may typically happen because of a
        # duplicate declaration.
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

        self.constraints.append(
            Constraint(
                kind=Constraint.Kind.equals, lhs=node.symbol.type, rhs=node.type,
                source_range=node.source_range))

    def visit_FunctionDeclaration(self, node):
        # Skip this node if its symbol wasn't been created, which may typically happen because of a
        # duplicate declaration.
        if node.symbol is None:
            return

        # Create the type of the declared function.
        domain = create_type(node.domain)
        codomain = create_type(node.codomain)
        node.type = types.FunctionType(domain, codomain, node.placeholders)

        self.constraints.append(
            Constraint(
                kind=Constraint.Kind.equals, lhs=node.symbol.type, rhs=node.type,
                source_range=node.source_range))


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
        if isinstance(node.symbol.type, types.TypeAlias):
            node.type = node.symbol.type.subject
            return node.type
        if isinstance(node.symbol.type, types.TypePlaceholder):
            node.type = node.symbol.type
            return node.type

        # Since we don't allow dynamic typing, the symbol of an identifier used as a type
        # should be either a type alias, or a type placeholder.
        raise exc.SemanticError(
            message=f"'{node.name}' is not a type", source_range=node.source_range)

    assert False, f"'{node}' does not represent a type"
