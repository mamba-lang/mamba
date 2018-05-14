class Type(object):

    def __init__(self, description=None):
        self._description = description

    def specialized(self, args: dict):
        return SpecializedType(type=self, args=args)

    def equals(self, other, memo: dict = None) -> bool:
        return self is other

    def to_string(self, memo: set) -> str:
        return f'<Type at {hex(id(self))}>'

    def __str__(self) -> str:
        if self._description is not None:
            return self._description
        return self.to_string(set())

    def __repr__(self) -> str:
        return str(self)


class SpecializedType(Type):

    def __init__(self, type: Type, args: dict):
        super().__init__()
        self.type = type
        self.args = args

    def to_string(self, memo: set) -> str:
        args = ', '.join(f'{key} = {type}' for key, type in self.args.items())
        return '[ ' + args + ' ]' + self.type.to_string(memo)


class GroundType(Type):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to_string(self, memo: set) -> str:
        return self.name


class ListType(Type):

    def __init__(self, element_type=None):
        super().__init__()
        self.placeholder = TypePlaceholder(name='Element')
        self.element_type = element_type or self.placeholder

    @property
    def placeholders(self):
        return [self.placeholder] if (self.element_type is self.placeholder) else None

    def equals(self, other, memo: dict = None) -> bool:
        if not isinstance(other, ListType):
            return False
        if self.element_type is None:
            return other.element_type is None
        return self.element_type.equals(other.element_type, memo=memo)

    def specialized(self, args: dict):
        if set(args.keys()) == { '_0' }:
            return ListType(element_type=args['_0'])
        else:
            return ListType(element_type=args['Element'])

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

    def equals(self, other, memo: dict = None) -> bool:
        if not isinstance(other, TypeAlias):
            return False
        return self.subject.equals(other.subject, memo=memo)

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

        for ph in self.placeholders:
            assert isinstance(ph, TypePlaceholder)

    def equals(self, other, memo: dict = None) -> bool:
        memo = memo if memo is not None else {}
        pair = (self, other)
        if pair in memo:
            return memo[pair]

        memo[pair] = True
        if (
            not isinstance(other, ObjectType) or
            len(self.properties) != len(other.properties) or
            len(self.placeholders) != len(other.placeholders)
        ):
            memo[pair] = False
            return False

        for prop_name in self.properties:
            if (
                (prop_name not in other.properties) or
                self.properties[prop_name].equals(other.properties[prop_name], memo=memo)
            ):
                memo[pair] = False
                return False

        for i in range(len(self.placeholders)):
            if self.placeholders[i].equals(other.placeholders[i], memo=memo):
                memo[pair] = False
                return False

        return True

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
        self.placeholders = placeholders or []

        for ph in self.placeholders:
            assert isinstance(ph, TypePlaceholder)

    def to_string(self, memo: set) -> str:
        if self.placeholders:
            placeholders = '[ ' + ', '.join(map(str, self.placeholders)) + ' ]'
        else:
            placeholders = ''
        return placeholders + f'{self.domain} -> {self.codomain}'


Nothing = GroundType('Nothing')
Bool    = GroundType('Bool')
Int     = GroundType('Int')
Float   = GroundType('Float')
String  = GroundType('String')
List    = ListType()
