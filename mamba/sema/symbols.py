from mamba import ast

from . import exc


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
            self.scopes[-1].insert(Symbol(name=placeholder))

        if isinstance(node.domain, ast.ObjectType):
            for member in node.domain.members:
                if self.scopes[-1].contains(lambda s: s.name == member.name):
                    self.errors.append(exc.DuplicateDeclaration(
                        name=member.name, source_range=member.source_range))
                    continue
                parameter_symbol = Symbol(name=member.name)
                self.scopes[-1].insert(parameter_symbol)
                member.symbol = parameter_symbol

        # Visit the innards of the function declaration.
        self.generic_visit(node)
        self.scopes.pop()

    def visit_TypeDeclaration(self, node):
        # Add the name of the type to the current scope.
        symbol = self.scopes[-1].first(where=lambda s: s.name == node.name)
        if symbol is None:
            symbol = Symbol(name=node.name, overloadable=True)
            self.scopes[-1].insert(symbol)
        else:
            self.errors.append(exc.DuplicateDeclaration(
                name=node.name, source_range=node.source_range))
            return
        node.symbol = symbol

        # Push a new scope for the type itself, and insert its generic placeholders into.
        self.scopes.append(Scope(parent=self.scopes[-1]))
        for placeholder in node.placeholders:
            self.scopes[-1].insert(Symbol(name=placeholder))

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


class Symbol(object):

    def __init__(self, name: str, type = None, overloadable: bool = False):
        self.name = name
        self.type = type
        self.overloadable = overloadable


class Scope(object):

    def __init__(self, parent = None, symbols = None):
        self.parent = parent
        self.symbols = set(symbols) if symbols is not None else set()

    def insert(self, symbol: Symbol):
        self.symbols.add(symbol)

    def contains(self, predicate: callable) -> bool:
        return self.first(where=predicate) is not None

    def first(self, where: callable) -> Symbol:
        for symbol in self.symbols:
            if where(symbol):
                return symbol
        return None


builtin_scope = Scope(symbols={
    Symbol(name='Object'),
    Symbol(name='Bool'),
    Symbol(name='Int'),
    Symbol(name='Float'),
    Symbol(name='String'),
    Symbol(name='List'),
    Symbol(name='Set'),
})
