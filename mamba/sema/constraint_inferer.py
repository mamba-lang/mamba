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
        self.signature_visitor = _SignatureConstraintInferer()

    def visit_TypeDeclaration(self, node):
        # The type of the node's symbol should be an alias, created during the scope building pass.
        assert isinstance(node.symbol.type, types.TypeAlias)

        # Create the declared type.
        try:
            self.signature_visitor.visit(node.body)
        except exc.SemanticError as e:
            self.errors.append(e)
            return

        # If the node has generic placeholders, add them to the created type.
        # FIXME (node.placeholders)

        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.symbol.type.subject,
            rhs=node.body.type,
            source_range=node.source_range))

    def visit_FunctionDeclaration(self, node):
        # Skip this node if its symbol wasn't been created due to a problem during symbol binding.
        if node.symbol is None:
            return

        # Create the type of the declared function.
        try:
            self.signature_visitor.visit(node.domain)
            self.signature_visitor.visit(node.codomain)
        except exc.SemanticError as e:
            self.errors.append(e)
            return
        node.type = types.FunctionType(node.domain.type, node.codomain.type, node.placeholders)

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
            rhs=node.domain.type,
            source_range=node.source_range))

        self.visit(node.body)

        # Create a conformity constraint between the return type of the function and that of the
        # function's body.
        self.constraints.append(Constraint(
            kind=Constraint.Kind.conforms,
            lhs=node.body.type,
            rhs=node.codomain.type,
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
            # An object `{ right: T }` with `right` the value of the right operand must conform to
            # the type of the left operand. For instance, `{ name = "Pikachu", level = 0 } . level`
            # implies `{ level: Int } ⊂ { name: String, level: Int }`.
            assert isinstance(node.right, ast.ScalarLiteral)
            obj_ty = types.ObjectType(properties={node.right.value: node.type})
            self.constraints.append(Constraint(
                kind=Constraint.Kind.conforms,
                lhs=obj_ty,
                rhs=node.left.type,
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
        node.type = types.TypeVariable()

        # Create a function type for the callee.
        arg_ty = types.TypeVariable()
        ret_ty = types.TypeVariable()
        fun_ty = types.FunctionType(domain=arg_ty, codomain=ret_ty)
        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.callee.type,
            rhs=fun_ty,
            source_range=node.source_range))

        # The argument of the call must conform to the function's domain, and the node itself must
        # be equal to the function's codomain.
        self.constraints.append(Constraint(
            kind=Constraint.Kind.conforms,
            lhs=node.argument.type,
            rhs=arg_ty,
            source_range=node.source_range))
        self.constraints.append(Constraint(
            kind=Constraint.Kind.equals,
            lhs=node.type,
            rhs=ret_ty,
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

        # Build the type of the specialization arguments (if any).
        specialization_arguments = {}
        if node.specializers:
            for key, child in node.specializers.items():
                self.signature_visitor.visit(child)
                specialization_arguments[key] = child.type

        # Create specialization constraints.
        node.type = types.TypeVariable()
        constraints = [
            Constraint(
                kind=Constraint.Kind.specializes,
                lhs=node.type,
                rhs=symbol.type,
                args=specialization_arguments,
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


class _SignatureConstraintInferer(ast.Visitor):
    """
    Visitor that extracts typing constraints for type signatures.

    Type signatures must be visited differently than expressions, in particular with respect to
    identifiers.
    """

    def visit_UnionType(self, node):
        self.generic_visit(node)
        node.type = types.UnionType([child.type for child in node.types])

    def visit_ObjectType(self, node):
        # Process the object's properties.
        properties = {}
        for prop in node.properties:
            # Make sure the same property doesn't appear twice in the object type.
            assert isinstance(prop, ast.ObjectTypeProperty)
            if prop.name in properties:
                raise exc.DuplicateDeclaration(name=prop.name, source_range=prop.source_range)

            # Create the property's type if it has an annotation.
            if prop.annotation is None:
                properties[prop.name] = types.TypeVariable()
            else:
                self.visit(prop.annotation)
                properties[prop.name] = prop.annotation.type

        # Create the object type.
        node.type = types.ObjectType(properties=properties)

    def visit_Identifier(self, node):
        # Make sure the symbol is bound.
        if (node.scope is None) or not node.scope[node.name]:
            raise exc.UnboundName(name=node.name, source_range=node.source_range)

        # The symbol should not be overloaded, as function names can't be used as type signatures.
        symbols = node.scope[node.name]
        if len(symbols) > 1:
            raise exc.SemanticError(
                message=f"'{node.name}' is not a type",
                source_range=node.source_range)
        symbol = symbols[0]

        # Since we don't allow dynamic typing, the symbol of an type identifier should be either an
        # alias or a placeholder, created during the scope building pass.
        if isinstance(symbol.type, types.TypeAlias):
            node.type = symbol.type.subject
        elif isinstance(symbol.type, types.TypePlaceholder):
            node.type = symbol.type
        else:
            raise exc.SemanticError(
                message=f"'{node.name}' is not a type",
                source_range=node.source_range)

        # Handle specialization arguments.
        if node.specializers:
            # Take into account the possible use of the syntactic sugar that consists of omitting
            # the name of the placeholder when there's only one (e.g. `List[Int]`).
            names = set(node.specializers)
            if names != { '_0' }:
                # Check for extraneous arguments.
                extraneous = names - set(getattr(node.type, 'placeholders', []))
                if extraneous:
                    raise exc.SemanticError(
                        message=f'extraneous explicit specializations: {extraneous}',
                        source_range=node.source_range)

            # Build the type of the specialization arguments.
            specialization_arguments = {}
            for key, child in node.specializers.items():
                self.visit(child)
                specialization_arguments[key] = child.type

            # Apply the specialization arguments.
            node.type = node.type.specialized(args=specialization_arguments)

    def visit_Nothing(self, node):
        node.type = types.Nothing
