class GroundType(object):

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)


class TypeVariable(object):

    def __repr__(self) -> str:
        return str(self)


class TypeAlias(object):

    def __init__(self, subject):
        self.subject = subject

    def __str__(self) -> str:
        return str(self.subject)

    def __repr__(self) -> str:
        return str(self)


class TypePlaceholder(object):

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class ObjectType(object):

    def __init__(self, properties=None, placeholders=None):
        self.properties = properties or {}
        self.placeholders = placeholders or []

    def __str__(self) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''

        # FIXME: Handle infinite recursions in the object representation.
        props = [f'{key}: _' for key, _ in self.properties.items()]
        return placeholders + '{ ' + ', '.join(props) + ' }'


class UnionType(object):

    def __init__(self, types):
        self.types = types

    def __str__(self) -> str:
        return ' | '.join([str(t) for t in self.types])


class FunctionType(object):

    def __init__(self, domain, codomain, placeholders=None):
        self.domain = domain
        self.codomain = codomain
        self.placeholders = placeholders

    def __str__(self) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''

        return placeholders + f'{self.domain} -> {self.codomain}'


Bool   = GroundType('Bool')
Int    = GroundType('Int')
Float  = GroundType('Float')
String = GroundType('String')
