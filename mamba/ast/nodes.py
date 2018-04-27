from mamba.lexer.lexer import SourceRange
from mamba.lexer.token import Token


class Node(object):

    _fields = tuple()

    def __init__(self, source_range: SourceRange):
        self.source_range = source_range


class TypedNode(object):

    @property
    def type(self):
        return getattr(self, '_type', None)

    @type.setter
    def type(self, value):
        setattr(self, '_type', value)


class NamedNode(object):

    @property
    def symbol(self):
        return getattr(self, '_symbol', None)

    @symbol.setter
    def symbol(self, value):
        setattr(self, '_symbol', value)


class Module(Node):

    _fields = ('declarations',)

    def __init__(self, declarations: list, source_range: SourceRange):
        super().__init__(source_range)
        self.declarations = declarations

    def __str__(self) -> str:
        return '\n'.join([str(d) for d in self.declarations])


class ObjectType(Node):

    _fields = ('properties',)

    def __init__(self, properties: list, source_range: SourceRange):
        super().__init__(source_range)
        self.properties = properties

    def __str__(self) -> str:
        return '{ ' + ', '.join([str(p) for p in self.properties]) + ' }'


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


class FunctionDeclaration(Node, NamedNode):

    _fields = ('name', 'placeholders', 'domain', 'codomain', 'body',)

    def __init__(
        self,
        name: str, placeholders: list, domain: Node, codomain: Node, body: Node,
        source_range: SourceRange):

        super().__init__(source_range)
        self.name = name
        self.placeholders = placeholders
        self.domain = domain
        self.codomain = codomain
        self.body = body

    def __str__(self) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''
        return f'func {self.name}{placeholders} {self.domain} -> {self.codomain} = {self.body}'


class TypeDeclaration(Node, NamedNode):

    _fields = ('name', 'placeholders', 'body',)

    def __init__(self, name: str, placeholders: list, body: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.placeholders = placeholders
        self.body = body

    def __str__(self) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''
        return f'type {self.name}{placeholders} = {self.body}'


class ClosureExpression(Node, TypedNode):

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


class InfixExpression(Node, TypedNode):

    _fields = ('operator', 'left', 'right',)

    def __init__(self, operator: Token, left: Node, right: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f'{self.left} {self.operator.value} {self.right}'


class PrefixExpression(Node, TypedNode):

    _fields = ('operator', 'operand',)

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operator.value}{self.operand}'


class PostfixExpression(Node, TypedNode):

    _fields = ('operator', 'operand',)

    def __init__(self, operator: Token, operand: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.operator = operator
        self.operand = operand

    def __str__(self) -> str:
        return f'{self.operand}{self.operator.value}'


class CallExpression(Node, TypedNode):

    _fields = ('callee', 'argument',)

    def __init__(self, callee: Node, argument: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.callee = callee
        self.argument = argument

    def __str__(self) -> str:
        if self.argument is not None:
            return f'{self.callee} {self.argument}'
        return f'{self.callee} _'


class IfExpression(Node, TypedNode):

    _fields = ('condition', 'then', 'else_')

    def __init__(self, condition: Node, then: Node, else_: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.condition = condition
        self.then = then
        self.else_ = else_

    def __str__(self) -> str:
        return f'if {self.condition} then {self.then} else {self.else_}'


class MatchExpression(Node, TypedNode):

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


class Binding(Node, TypedNode):

    _fields = ('name', 'annotation',)

    def __init__(self, name: str, annotation: Node, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.annotation = annotation

    def __str__(self) -> str:
        if self.annotation is not None:
            return f'let {self.name}: {self.annotation}'
        return f'let {self.name}'


class Identifier(Node, TypedNode, NamedNode):

    _fields = ('name',)

    def __init__(self, name: str, specializers: dict, source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.specializers = specializers

        # Altough they are named nodes, identifiers aren't associated with a symbol directly (i.e.
        # during symbol binding) because of overloading. Instead, we bind them to a scope which
        # contains all the symbols it may be bound to once type inference finishes.
        self.scope = None

    def __str__(self) -> str:
        if self.specializers:
            specs = ', '.join(f'{key} = {value}' for key, value in self.specializers.items())
            return f'{self.name}[ {specs} ]'
        else:
            return self.name


class ScalarLiteral(Node, TypedNode):

    _fields = tuple()

    def __init__(self, value: object, source_range: SourceRange):
        super().__init__(source_range)
        self.value = value

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        if isinstance(self.value, bool):
            return 'true' if self.value else 'false'
        return str(self.value)


class ListLiteral(Node, TypedNode):

    _fields = ('items',)

    def __init__(self, items: list, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        items = ', '.join([str(i) for i in self.items])
        return f'[ {items} ]'


class ObjectLiteral(Node, TypedNode):

    _fields = ('items',)

    def __init__(self, items: list, source_range: SourceRange):
        super().__init__(source_range)
        self.items = items

    def __str__(self) -> str:
        pairs = []
        for key, value in self.items:
            if isinstance(key, ScalarLiteral):
                pairs.append(f'{key}: {value}')
            else:
                pairs.append((f'[ {key} ]: {value}'))
        return '{ ' + ', '.join(pairs) + ' }'


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
