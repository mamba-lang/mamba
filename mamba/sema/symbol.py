from . import types


class Symbol(object):

    def __init__(self, name: str, type = None, overloadable: bool = False):
        self.name = name
        self.type = type or types.TypeVariable()
        self.overloadable = overloadable


class Scope(object):

    def __init__(self, parent = None, symbols = None):
        self.parent = parent
        self.symbols = symbols if symbols is not None else {}

    def insert(self, symbol: Symbol):
        self.symbols[symbol.name] = self.symbols.get(symbol.name, []) + [symbol]

    def contains(self, predicate: callable) -> bool:
        return self.first(where=predicate) is not None

    def first(self, where: callable) -> Symbol:
        for name in self.symbols:
            for symbol in self.symbols[name]:
                if where(symbol):
                    return symbol
        return None

    def find_scope_of(self, name) -> Symbol:
        if name in self.symbols:
            return self
        if self.parent:
            return self.parent.find_scope_of(name)
        return None

    def __getitem__(self, name):
        return self.symbols.get(name)


# `.` is a special function that allows access to object properties. It's signature can't be
# formally expressed within Mamba's type system, as it would depend on the name of the requested
# property. In fact, the set of overloads of `.` is an infinite set of signatures, described as:
#
#     ∀a ∈ Σ*, . [T] { lhs: { a: T }, rhs: String } -> T
#
# where Σ is the alphabet of character allowed in a string.
dot_symbol = Symbol(
    name='.',
    overloadable=True,
    type=types.Type(description='[built-in dot operator]'))

# `!` is a special function that allows unchecked access to object properties. Just as `.`, its
# signature can't be formally expressed withing Mamba's type system in general, hence the use of a
# built-in type.
exclamation_symbol = Symbol(
    name='!',
    overloadable=True,
    type=types.Type(description='[built-in exclamation operator]'))

# However, if the left operand is a list, and the right operand an integer (i.e. a list index),
# then the type of the result might be inferred, which is why the symbol is overloaded.
getitem_symbol = Symbol(
    name='!',
    overloadable=True,
    type=types.FunctionType(
        domain       = types.ObjectType({ 'lhs': types.List, 'rhs': types.Int }),
        codomain     = types.List.placeholders[0],
        placeholders = types.List.placeholders))


builtin_scope = Scope(symbols={
    # The built-in types.
    'Object': [Symbol(name='Object', type=types.TypeAlias(types.ObjectType()))],
    'Bool'  : [Symbol(name='Bool'  , type=types.TypeAlias(types.Bool))],
    'Int'   : [Symbol(name='Int'   , type=types.TypeAlias(types.Int))],
    'Float' : [Symbol(name='Float' , type=types.TypeAlias(types.Float))],
    'String': [Symbol(name='String', type=types.TypeAlias(types.String))],
    'List'  : [Symbol(name='List'  , type=types.TypeAlias(types.List))],

    # `.` is the special operator that allows access to object properties.
    '.'     : [dot_symbol],

    # `!` is the special operator that allows unchecked access to object properties.
    '!'     : [exclamation_symbol, getitem_symbol],

    # Arithmetic operators.
    '+'     : [
        Symbol(
            name='+',
            overloadable=True,
            type=types.FunctionType(
                domain   = types.ObjectType({ 'lhs': types.Int, 'rhs': types.Int }),
                codomain = types.Int)),
        Symbol(
            name='+',
            overloadable=True,
            type=types.FunctionType(
                domain   = types.ObjectType({ 'lhs': types.Float, 'rhs': types.Float }),
                codomain = types.Float)),
    ],

    # The `print` function.
    'print' : [
        Symbol(
            name='print',
            overloadable=True,
            type=types.FunctionType(
                domain   = types.ObjectType({ 'item': types.ObjectType() }),
                codomain = types.Nothing)),
    ],
})
