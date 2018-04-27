class Type(object):

    def __str__(self) -> str:
        return self.to_string(set())

    def __repr__(self) -> str:
        return str(self)


class GroundType(Type):

    def __init__(self, name: str, placeholders=None):
        self.name = name
        self.placeholders = placeholders or []

    def to_string(self, memo: set) -> str:
        if self.placeholders:
            return '[ ' + ', '.join(self.placeholders) + ' ]' + self.name
        else:
            return self.name


class TypeVariable(Type):

    def to_string(self, memo: set) -> str:
        return '__' + hex(id(self))[-6:]


class TypeAlias(object):

    def __init__(self, subject):
        self.subject = subject

    def to_string(self, memo: set) -> str:
        return f'~{self.subject.to_string(memo)}'


class TypePlaceholder(Type):

    def __init__(self, name: str):
        self.name = name

    def to_string(self, memo: set) -> str:
        return self.name


class ObjectType(Type):

    def __init__(self, properties=None, placeholders=None):
        self.properties = properties or {}
        self.placeholders = placeholders or []

    def to_string(self, memo: set) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''

        if self in memo:
            return placeholders + '{ ... }'
        memo.add(self)

        props = [f'{key}: {value.to_string(memo)}' for key, value in self.properties.items()]
        return placeholders + '{ ' + ', '.join(props) + ' }'


class UnionType(Type):

    def __init__(self, types):
        self.types = types

    def to_string(self, memo: set) -> str:
        return ' | '.join([t.to_string(memo) for t in self.types])


class FunctionType(Type):

    def __init__(self, domain, codomain, placeholders=None):
        self.domain = domain
        self.codomain = codomain
        self.placeholders = placeholders

    def to_string(self, memo: set) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''
        return placeholders + f'{self.domain.to_string(memo)} -> {self.codomain.to_string(memo)}'


Nothing = GroundType('Nothing')
Bool    = GroundType('Bool')
Int     = GroundType('Int')
Float   = GroundType('Float')
String  = GroundType('String')
List    = GroundType('List', placeholders=['Element'])
Set     = GroundType('Set', placeholders=['Element'])
