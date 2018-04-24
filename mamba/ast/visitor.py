from .nodes import Node


class Visitor(object):
    """
    A node visitor base class that walks the AST and calls a visitor function for every node.

    This cleass is heavily inspired by Python's ast.NodeVisitor class. Default the visitor
    functions for the nodes should be called ``'visit_'`` followed by the class name of the node.
    """

    def visit(self, node: Node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)

    def generic_visit(self, node: Node):
        for field in node._fields:
            value = getattr(node, field)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Node):
                        self.visit(item)
            elif isinstance(value, Node):
                self.visit(value)
