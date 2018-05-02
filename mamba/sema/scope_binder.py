from mamba import ast

from .exc import UnboundName


class ScopeBinder(ast.Visitor):
    """
    Static analysis pass that binds all identifiers to a particular symbol (and scope).
    """

    def __init__(self):
        self.scopes = []
        self.errors = []

    def visit_Module(self, node):
        self.scopes.append(node.inner_scope)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_FunctionDeclaration(self, node):
        self.scopes.append(node.inner_scope)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_TypeDeclaration(self, node):
        self.scopes.append(node.inner_scope)
        self.generic_visit(node)
        self.scopes.pop()

    def visit_Identifier(self, node):
        # Look for the symbol to which bind the identifier.
        scope = self.scopes[-1].find_scope_of(node.name)
        if scope is not None:
            node.scope = scope
            self.generic_visit(node)
        else:
            self.errors.append(UnboundName(name=node.name, source_range=node.source_range))

    def visit_ArgRef(self, node):
        # Look for the symbol to which bind the argument reference.
        scope = self.scopes[-1].find_scope_of('$')
        if scope is not None:
            assert len(scope['$']) == 1
            node.symbol = scope['$'][0]
        else:
             self.errors.append(UnboundName(name='$', source_range=node.source_range))
