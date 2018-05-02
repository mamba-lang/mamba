from mamba.ast import Transformer


class Sanitizer(Transformer):

    def visit_ParenthesizedNode(self, node):
        child = node.node
        kwargs = { name: getattr(child, name) for name in child._fields }
        return child.__class__(source_range=node.source_range, **kwargs)
