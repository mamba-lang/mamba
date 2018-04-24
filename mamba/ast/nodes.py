from mamba.lexer.lexer import SourceRange
from mamba.lexer.token import Token


class Node(object):

    _fields = tuple()

    def __init__(self, source_range: SourceRange):
        self.source_range = source_range


class Module(Node):

    _fields = ('declarations',)

    def __init__(self, declarations: list, source_range: SourceRange):
        super().__init__(source_range)
        self.declarations = declarations

    def __str__(self) -> str:
        return '\n'.join([str(d) for d in self.declarations])


class ObjectType(Node):

    _fields = ('members',)

    def __init__(self, members: list, source_range: SourceRange):
        super().__init__(source_range)
        self.members = members

    def __str__(self) -> str:
        return '{ ' + ', '.join([str(m) for m in self.members]) + ' }'


class UnionType(Node):

    _fields = ('types',)

    def __init__(self, types: list, source_range: SourceRange):
        super().__init__(source_range)
        self.types = types

    def __str__(self) -> str:
        return ' | '.join([str(t) for t in self.types])


class ObjectProperty(Node):

    _fields = ('name', 'annotation',)

    def __init__(self, name: str, annotation: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.annotation = annotation

    def __str__(self) -> str:
        if self.annotation:
            return f'{self.name}: {self.annotation}'
        return self.name


class FunctionDeclaration(Node):

    _fields = ('name', 'domain', 'codomain', 'body',)

    def __init__(self, name: str, domain: Node, codomain: Node, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.domain = domain
        self.codomain = codomain
        self.body = body

    def __str__(self) -> str:
        return f'func {self.name} {self.domain} -> {self.codomain} = {self.body}'


class TypeDeclaration(Node):

    _fields = ('name', 'body',)

    def __init__(self, name: str, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.body = body

    def __str__(self) -> str:
        return f'type {self.name} = {self.body}'


class ClosureExpression(Node):

    _fields = ('domain', 'codomain', 'body',)

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

    _fields = ('operator', 'left', 'right',)

    def __init__(self, operator: Token, left: Node, right: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f'{self.left} {self.operator.value} {self.right}'


class PrefixExpression(Node):

    _fields = ('operator', 'operand',)

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operator.value}{self.operand}'


class PostfixExpression(Node):

    _fields = ('operator', 'operand',)

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operand}{self.operator.value}'


class CallExpression(Node):

    _fields = ('callee', 'argument',)

    def __init__(self, callee: Node, argument: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.callee = callee
        self.argument = argument

    def __str__(self) -> str:
        if self.argument is not None:
            return f'{self.callee} {self.argument}'
        return f'{self.callee} _'


class IfExpression(Node):

    _fields = ('condition', 'then', 'else_')

    def __init__(self, condition: Node, then: Node, else_: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.condition = condition
        self.then = then
        self.else_ = else_

    def __str__(self) -> str:
        return f'if {self.condition} then {self.then} else {self.else_}'


class MatchExpression(Node):

    _fields = ('subject', 'cases',)

    def __init__(self, subject: Node, cases: list, source_range: SourceRange):
        super().__init__(source_range)
        self.subject = subject
        self.cases = cases

    def __str__(self) -> str:
        cases = '\n'.join([str(c) for c in self.cases]).split('\n')
        cases = [' ' + c for c in cases]
        cases = '\n'.join(cases)
        return f'match {self.subject}\n{cases}'


class WhenCase(Node):

    _fields = ('pattern', 'body',)

    def __init__(self, pattern: Node, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.pattern = pattern
        self.body = body

    def __str__(self) -> str:
        return f'when {self.pattern} then {self.body}'


class ElseCase(Node):

    _fields = ('body',)

    def __init__(self, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.body = body

    def __str__(self) -> str:
        return f'else {self.body}'


class Binding(Node):

    _fields = ('name', 'annotation',)

    def __init__(self, name: str, annotation: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.annotation = annotation

    def __str__(self) -> str:
        if self.annotation is not None:
            return f'let {self.name}: {self.annotation}'
        return f'let {self.name}'


class Identifier(Node):

    _fields = ('name',)

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

    _fields = tuple()

    def __init__(self, value: object, source_range: SourceRange):
        super().__init__(source_range)
        self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)


class ListLiteral(Node):

    _fields = ('items',)

    def __init__(self, items: list, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        items = ', '.join([str(i) for i in self.items])
        return f'[ {items} ]'


class ObjectLiteral(Node):

    _fields = ('items',)

    def __init__(self, items: dict, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        items = ', '.join([f'{key} = {value}' for key, value in self.items.items()])
        return '{ ' + items + ' }'


class Nothing(Node):

    _fields = tuple()

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)

    def __str__(self) -> str:
        return '_'


class ParenthesizedNode(Node):

    _fields = ('node',)

    def __init__(self, node: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.node = node

    def __str__(self) -> str:
        return f'({self.node})'
