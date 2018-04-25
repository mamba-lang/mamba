from mamba import ast

from . import exc
from . import types
from .symbol import Scope, Symbol, builtin_scope


class SymbolBinder(ast.Visitor):
    """
    The static analysis pass that binds all identifiers to a particular symbol.

    This steps allows to check for unbound variables, duplicate declarations, and is also required
    to perform type inference, so as to map type aliases to their respective definition.
    """

    def __init__(self):
        self.scopes = [builtin_scope]
        self.errors = []

    def visit_Module(self, node):
        # Push a new scope, so that symbols of the module can shadow built-in ones.
        self.scopes.append(Scope(parent=self.scopes[-1]))
        self.generic_visit(node)
        self.scopes.pop()

    def visit_FunctionDeclaration(self, node):
        # Add the name of the function to the current scope.
        symbol = self.scopes[-1].first(where=lambda s: s.name == node.name)
        if symbol is None:
            symbol = Symbol(name=node.name, overloadable=True)
            self.scopes[-1].insert(symbol)
        elif not symbol.overloadable:
            self.errors.append(exc.DuplicateDeclaration(
                name=node.name, source_range=node.source_range))
            return
        node.symbol = symbol

        # Push a new scope for the function itself.
        self.scopes.append(Scope(parent=self.scopes[-1]))

        # Insert the function arguments and generic placeholders into its scope.
        for placeholder in node.placeholders:
            ty = types.TypePlaceholder(name=placeholder)
            self.scopes[-1].insert(Symbol(name=placeholder, type=ty))

        if isinstance(node.domain, ast.ObjectType):
            for prop in node.domain.properties:
                if self.scopes[-1].contains(lambda s: s.name == prop.name):
                    self.errors.append(exc.DuplicateDeclaration(
                        name=prop.name, source_range=prop.source_range))
                    continue
                parameter_symbol = Symbol(name=prop.name)
                self.scopes[-1].insert(parameter_symbol)
                prop.symbol = parameter_symbol

        # Visit the innards of the function declaration.
        self.generic_visit(node)
        self.scopes.pop()

    def visit_TypeDeclaration(self, node):
        # Add the name of the type to the current scope.
        symbol = self.scopes[-1].first(where=lambda s: s.name == node.name)
        if symbol is None:
            symbol = Symbol(name=node.name, type=types.TypeAlias(types.TypeVariable()))
            self.scopes[-1].insert(symbol)
        else:
            self.errors.append(exc.DuplicateDeclaration(
                name=node.name, source_range=node.source_range))
            return
        node.symbol = symbol

        # Push a new scope for the type itself, and insert its generic placeholders into.
        self.scopes.append(Scope(parent=self.scopes[-1]))
        for placeholder in node.placeholders:
            ty = types.TypePlaceholder(name=placeholder)
            self.scopes[-1].insert(Symbol(name=placeholder, type=ty))

        # Visit the innards of the type declaration.
        self.generic_visit(node)
        self.scopes.pop()

    def visit_Identifier(self, node):
        # Look for the symbol to which bind the identifier.
        for scope in reversed(self.scopes):
            symbol = scope.first(where=lambda s: s.name == node.name)
            if symbol is not None:
                node.symbol = symbol
                self.generic_visit(node)
                return

        # The identifier is unbound.
        self.errors.append(exc.UnboundName(name=node.name, source_range=node.source_range))
