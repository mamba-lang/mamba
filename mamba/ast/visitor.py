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
        return visitor(node)

    def generic_visit(self, node: Node):
        for field in node._fields:
            value = getattr(node, field)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Node):
                        self.visit(item)
            if isinstance(value, dict):
                for key, item in value.items():
                    if isinstance(item, Node):
                        self.visit(item)
            elif isinstance(value, Node):
                self.visit(value)


class Transformer(Visitor):
    """
    A subclass of the AST visitor that allows modification of the nodes.

    This cleass is heavily inspired by Python's ast.NodeTransformer class. Default the transformer
    functions for the nodes should be called ``'visit_'`` followed by the class name of the node.
    """

    def generic_visit(self, node: Node):
        for field in node._fields:
            value = getattr(node, field)
            if isinstance(value, list):
                new_values = []
                for item in value:
                    if isinstance(item, Node):
                        new_value = self.visit(item)
                        if new_value is None:
                            continue
                        elif not isinstance(new_value, Node):
                            new_values.extend(new_value)
                            continue
                    new_values.append(item)
                value[:] = new_values
            if isinstance(value, dict):
                new_values = {}
                for key, item in value.items():
                    if isinstance(item, Node):
                        new_item = self.visit(item)
                        if new_item is None:
                            continue
                        else:
                            new_values[key] = new_item
                            continue
                    new_values.append(item)
                value.clear()
                value.update(**new_values)
            elif isinstance(value, Node):
                new_value = self.visit(value)
                if new_value is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_value)
        return node
