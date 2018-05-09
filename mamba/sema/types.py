from .exc import SpecializationError


class Type(object):

    def __init__(self, description=None):
        self._description = description

    def to_string(self, memo: set) -> str:
        return f'<Type at {hex(id(self))}>'

    def __str__(self) -> str:
        if self._description is not None:
            return self._description
        return self.to_string(set())

    def __repr__(self) -> str:
        return str(self)


class GroundType(Type):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to_string(self, memo: set) -> str:
        return self.name


class ListType(Type):

    def __init__(self, element_type=None):
        super().__init__()
        self.element_type = element_type

    @property
    def placeholders(self):
        return ['Element'] if (self.element_type is None) else None

    def to_string(self, memo: set) -> str:
        if self.element_type:
            return f'List[ Element = {self.element_type} ]'
        else:
            return 'List'


class TypeVariable(Type):

    next_id = 0

    def __init__(self):
        super().__init__()
        self.id = TypeVariable.next_id
        TypeVariable.next_id += 1

    def to_string(self, memo: set) -> str:
        return f'__{self.id}'


class TypeAlias(object):

    def __init__(self, subject):
        super().__init__()
        self.subject = subject

    def to_string(self, memo: set) -> str:
        return f'~{self.subject.to_string(memo)}'


class TypePlaceholder(Type):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to_string(self, memo: set) -> str:
        return self.name


class ObjectType(Type):

    def __init__(self, properties=None, placeholders=None):
        super().__init__()
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

    def __len__(self):
        return len(self.properties)

    def __iter__(self):
        return iter(self.properties)

    def __getitem__(self, item):
        return self.properties[item]


class UnionType(Type):

    def __init__(self, types):
        super().__init__()
        self.types = types

    def to_string(self, memo: set) -> str:
        return ' | '.join(str(t) for t in self.types)


class FunctionType(Type):

    def __init__(self, domain, codomain, placeholders=None):
        super().__init__()
        self.domain = domain
        self.codomain = codomain
        self.placeholders = placeholders

    def to_string(self, memo: set) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(self.placeholders) + ' ]'
        else:
            placeholders = ''
        return placeholders + f'{self.domain} -> {self.codomain}'


def specialize(generic, pattern, memo=None):
    # Avoid infinite recursions.
    memo = memo if memo is not None else {}
    if generic in memo:
        return memo[generic]

    # If the generic type is a placeholder, use the pattern if possible.
    if isinstance(generic, TypePlaceholder):
        # Make sure the generic type is compatible with the given pattern, for every occurence of a
        # given type placeholder.
        if (generic in memo) and not (pattern == memo[generic]):
            raise SpecializationError()
        memo[generic] = pattern
        return pattern

    # If the generic type or the specialization pattern is a variable, return it.
    if isinstance(generic, TypeVariable) or isinstance(pattern, TypeVariable):
        return generic

    if isinstance(generic, FunctionType) and isinstance(pattern, FunctionType):
        domain = specialize(generic.domain, pattern.domain, memo=memo)
        codomain = specialize(generic.codomain, pattern.codomain, memo=memo)
        return FunctionType(domain=domain, codomain=codomain)

    assert False


Nothing = GroundType('Nothing')
Bool    = GroundType('Bool')
Int     = GroundType('Int')
Float   = GroundType('Float')
String  = GroundType('String')
List    = ListType()
