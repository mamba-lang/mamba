from mamba import ast

from . import exc
from . import types
from .symbol import Scope, Symbol, builtin_scope


class ScopeBuilder(ast.Visitor):
    """
    Static analysis pass that build the lexical scopes of a module, and fill them with the symbols
    that are declared within.

    This steps allows the scope binder to then bind identifiers to their correct scope and to
    identify unbound symbols.

    FIXME: Process other scope nodes (e.g. if-expressions).
    """

    def __init__(self):
        self.scopes = [builtin_scope]
        self.errors = []

    def visit_Module(self, node):
        # Push a new scope, so that symbols of the module can shadow built-in ones.
        node.inner_scope = Scope(parent=self.scopes[-1])
        self.scopes.append(node.inner_scope)
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
        node.inner_scope = Scope(parent=self.scopes[-1])
        self.scopes.append(node.inner_scope)

        # Insert the function argument reference and generic placeholders into its scope.
        for placeholder in node.placeholders:
            ty = types.TypePlaceholder(name=placeholder)
            self.scopes[-1].insert(Symbol(name=placeholder, type=ty))
        self.scopes[-1].insert(Symbol(name='$'))

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

        # Push a new scope for the type itself.
        node.inner_scope = Scope(parent=self.scopes[-1])
        self.scopes.append(node.inner_scope)

        # Insert the type generic placeholders into its scope.
        for placeholder in node.placeholders:
            ty = types.TypePlaceholder(name=placeholder)
            self.scopes[-1].insert(Symbol(name=placeholder, type=ty))

        # Visit the innards of the type declaration.
        self.generic_visit(node)
        self.scopes.pop()
