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
        props = [f'{key}: {value}' for key, value in self.properties.items()]
        return placeholders + '{ ' + ', '.join(props) + ' }'


Bool   = GroundType('Bool')
Int    = GroundType('Int')
Float  = GroundType('Float')
String = GroundType('String')
