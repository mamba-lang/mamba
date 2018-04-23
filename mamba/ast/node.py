from mamba.lexer.lexer import SourceRange
from mamba.lexer.token import Token


class Node(object):

    def __init__(self, source_range: SourceRange):
        self.source_range = source_range


class Module(Node):

    def __init__(self, declarations: list, source_range: SourceRange):
        super().__init__(source_range)
        self.declarations = declarations

    def __str__(self) -> str:
        return '\n'.join([str(d) for d in self.declarations])


class ObjectType(Node):

    def __init__(self, members: list, source_range: SourceRange):
        super().__init__(source_range)
        self.members = members

    def __str__(self) -> str:
        return '{ ' + ', '.join([str(m) for m in self.members]) + ' }'


class ObjectProperty(Node):

    def __init__(self, name: str, annotation: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.annotation = annotation

    def __str__(self) -> str:
        if self.annotation:
            return f'{self.name}: {self.annotation}'
        return self.name


class FunctionDeclaration(Node):

    def __init__(self, name: str, domain: Node, codomain: Node, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.domain = domain
        self.codomain = codomain
        self.body = body

    def __str__(self) -> str:
        return f'func {self.name} {self.domain} -> {self.codomain} = {self.body}'


class ClosureExpression(Node):

    def __init__(self, domain: Node, codomain: Node, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.domain = domain
        self.codomain = codomain
        self.body = body

    def __str__(self) -> str:
        result = str(self.domain)
        if self.codomain is not None:
            result += f' -> {self.codomain}'
        return result + f' => {self.body}'


class InfixExpression(Node):

    def __init__(self, operator: Token, left: Node, right: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f'{self.left} {self.operator.value} {self.right}'


class PrefixExpression(Node):

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operator.value}{self.operand}'


class PostfixExpression(Node):

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operand}{self.operator.value}'


class CallExpression(Node):

    def __init__(self, callee: Node, argument: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.callee = callee
        self.argument = argument

    def __str__(self) -> str:
        if self.argument is not None:
            return f'{self.callee} {self.argument}'
        return f'{self.callee} _'


class Identifier(Node):

    def __init__(self, name: str, specializers: list, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.specializers = specializers

    def __str__(self) -> str:
        if self.specializers:
            specs = ', '.join(self.specializers)
            return f'{self.name}[ {specs} ]'
        else:
            return self.name


class ScalarLiteral(Node):

    def __init__(self, value: object, source_range: SourceRange):
        super().__init__(source_range)
        self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)


class ListLiteral(Node):

    def __init__(self, items: list, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        items = ', '.join([str(i) for i in self.items])
        return f'[ {items} ]'


class ObjectLiteral(Node):

    def __init__(self, items: dict, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        items = ', '.join([f'{key} = {value}' for key, value in self.items.items()])
        return '{ ' + items + ' }'


class Nothing(Node):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)

    def __str__(self) -> str:
        return '_'


class ParenthesizedNode(Node):

    def __init__(self, node: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.node = node

    def __str__(self) -> str:
        return f'({self.node})'