from mamba import ast

from .constraint import Constraint
from .symbol import dot_symbol
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
        assert isinstance(node.symbol.type, types.TypeAlias)

        # Create the declared type.
        node.type = create_type(node.body)
        if node.placeholders:
            if isinstance(node.type, types.UnionType):
                for ty in node.type:
                    ty.placeholders = node.placeholders
            else:
                node.type.placeholders = node.placeholders

        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.symbol.type.subject,
            rhs=node.type,
            source_range=node.source_range))

        # Note that we do not recursively visit the body of a type declaration, as it has already
        # been processed by `create_type`.

    def visit_FunctionDeclaration(self, node):
        # Skip this node if its symbol wasn't been created due to a problem during symbol binding.
        if node.symbol is None:
            return

        # Create the type of the declared function.
        domain = create_type(node.domain)
        codomain = create_type(node.codomain)
        node.type = types.FunctionType(domain, codomain, node.placeholders)

        # Note that we do not recursively visit the domain/codomain of a function declaration, as
        # they already have been processed by `create_type`.

        # Create an equality constraint for the function's symbol.
        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.symbol.type,
            rhs=node.type,
            source_range=node.source_range))

        # Create an equality constraint for the function's arugment reference.
        argref_symbol = node.inner_scope['$'][0]
        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=argref_symbol.type,
            rhs=domain,
            source_range=node.source_range))

        self.visit(node.body)

        # Create a conformity constraint between the return type of the function and that of the
        # function's body.
        self.constraints.append(Constraint(
            kind=Constraint.Kind.conforms,
            lhs=node.body.type,
            rhs=codomain,
            source_range=node.body.source_range))

    def visit_InfixExpression(self, node):
        # Infer the types of the operands and operator.
        self.generic_visit(node)

        # The type of the expression itself is a variable.
        node.type = types.TypeVariable()

        # If the symbol of the operator is the built-in `.` function, the node should be treated
        # as a special case.
        symbols = node.operator.scope[node.operator.name]
        if dot_symbol in symbols:
            # The type of the left operand must conform to `{ right: T }`, where `right` is the
            # value of the right operand.
            assert isinstance(node.right, ast.ScalarLiteral)
            objTy = types.ObjectType(properties={node.right.value: node.type})
            self.constraints.append(Constraint(
                kind=Constraint.Kind.conforms,
                lhs=node.left.type,
                rhs=objTy,
                source_range=node.source_range))

            # FIXME: We also should consider the alternative where the right operand is a function
            # to be applied on the left one, so as to support "method calls". That is, if the infix
            # expression is `foo.bar`, then we should add an alternative constraint where `bar`'s
            # symbol is typed with a function `{ self: L } -> T` where `L` is the type of `foo` and
            # `T` that of the infix expression.

            return

        # Create a binary function for the operator, based on the type of the operands, which must
        # specialize the type of the operator.
        fn_ty = types.FunctionType(
            domain=types.ObjectType(properties={'lhs': node.left.type, 'rhs': node.right.type}),
            codomain=node.type)
        self.constraints.append(Constraint(
            kind=Constraint.Kind.specializes,
            lhs=node.operator.type,
            rhs=fn_ty,
            args=[],
            source_range=node.source_range))

    def visit_CallExpression(self, node):
        self.visit(node.callee)
        self.visit(node.argument)

        # Create a function type for the callee, based on the arguments of the node, which must
        # specialize the type of the callee.
        node.type = types.TypeVariable()
        fn_ty = types.FunctionType(domain=node.argument.type, codomain=node.type)
        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.callee.type,
            rhs=fn_ty,
            source_range=node.source_range))

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
        args = { name: create_type(ty) for name, ty in (node.specializers or {}) }

        # Note that we do not recursively visit the specializers of an identifier declaration, as
        # they already have been processed by `create_type`.

        # Create equality and specialization constraints.
        node.type = types.TypeVariable()
        constraints = [
            Constraint(
                kind=Constraint.Kind.specializes,
                lhs=node.type,
                rhs=symbol.type,
                args=args,
                source_range=node.source_range)
            for symbol in symbols
        ]
        if len(constraints) == 1:
            self.constraints.append(constraints[0])
        else:
            self.constraints.append(Constraint(
                kind=Constraint.Kind.disjunction,
                choices=constraints,
                source_range=node.source_range))

    def visit_ArgRef(self, node):
        node.type = node.symbol.type

    def visit_ScalarLiteral(self, node):
        if isinstance(node.value, bool):
            node.type = types.Bool
        elif isinstance(node.value, int):
            node.type = types.Int
        elif isinstance(node.value, float):
            node.type = types.Float
        elif isinstance(node.value, str):
            node.type = types.String
        else:
            assert False, f"unexpected scalar type '{type(node.value)}'"

    def visit_ObjectLiteral(self, node):
        props = {}
        for prop in node.properties:
            # The key of an object literal must be scalar literal (i.e. an object that can be typed
            # statically). This should have already been checked during the AST sanitizing.
            assert isinstance(prop.key, ast.ScalarLiteral), f"'{key}' is not a scalar literal"
            self.visit(prop.key)
            self.visit(prop.value)
            props[prop.key.value] = prop.value.type

        node.type = types.ObjectType(properties=props)


def create_type(node):
    if isinstance(node, ast.UnionType):
        return types.UnionType([create_type(t) for t in node.types])

    if isinstance(node, ast.ObjectType):
        properties = {}
        for prop in node.properties:
            assert isinstance(prop, ast.ObjectTypeProperty)
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

    if isinstance(node, ast.Nothing):
        return types.Nothing

    raise exc.SemanticError(message=f"'{node}' is not a type", source_range=node.source_range)
