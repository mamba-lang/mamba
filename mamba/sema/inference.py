from mamba import ast

from . import exc
from . import types


class TypeBuilder(ast.Visitor):

    def __init__(self):
        self.errors = []

    def visit_TypeDeclaration(self, node):
        # Skip this node if its symbol wasn't been created.
        if node.symbol is None:
            return

        node.symbol.type = types.TypeAlias(create_type(node.body))
        self.generic_visit(node)


def create_type(node: ast.Node):
    if isinstance(node, ast.ObjectType):
        members = {}
        for member in node.members:
            assert isinstance(member, ast.ObjectProperty)
            if member.name in members:
                raise exc.DuplicateDeclaration(name=member.name, source_range=member.source_range)
            elif member.annotation is None:
                members[member.name] = types.TypeVariable()
            else:
                members[member.name] = create_type(member.annotation)

        return types.ObjectType(members)

    if isinstance(node, ast.Identifier):
        ty = node.symbol.type
        if isinstance(ty, types.TypeAlias):
            return ty.subject
        if isinstance(ty, types.TypePlaceholder):
            return ty
        assert False, f"unexpected type for identifier: '{ty}'"


    assert False, f"'{node}' does not represent a type"
