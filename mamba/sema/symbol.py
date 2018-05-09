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


# Note: `.` is a special function that allows access to object properties. It's signature can't be
# formally expressed within Mamba's type system, as it would depend on the name of the requested
# property. In fact, the set of overloads of `.` is an infinite set of signatures, described as:
#
#     ∀a ∈ Σ*, . [T] { lhs: { a: T }, rhs: String } -> T
#
# where Σ is the alphabet of character allowed in a string.
dot_symbol = Symbol(name='.', type=types.Type(description='[built-in dot operator]'))


builtin_scope = Scope(symbols={
    # The built-in types.
    'Object': [Symbol(name='Object', type=types.TypeAlias(types.ObjectType()))],
    'Bool'  : [Symbol(name='Bool'  , type=types.TypeAlias(types.Bool))],
    'Int'   : [Symbol(name='Int'   , type=types.TypeAlias(types.Int))],
    'Float' : [Symbol(name='Float' , type=types.TypeAlias(types.Float))],
    'String': [Symbol(name='String', type=types.TypeAlias(types.String))],
    'List'  : [Symbol(name='List'  , type=types.TypeAlias(types.List))],
    'Set'   : [Symbol(name='Set'   , type=types.TypeAlias(types.Set))],

    # `.` is the special operator that allows access to object properties.
    '.'     : [dot_symbol],

    # Arithmetic operators.
    '+'     : [
        Symbol(name='+', type=types.FunctionType(
            domain   = types.ObjectType({ 'lhs': types.Int, 'rhs': types.Int }),
            codomain = types.Int)),
        Symbol(name='+', type=types.FunctionType(
            domain   = types.ObjectType({ 'lhs': types.Float, 'rhs': types.Float }),
            codomain = types.Float)),
    ],

    # The `print` function.
    'print' : [
        Symbol(name='print', type=types.FunctionType(
            domain   = types.ObjectType({ 'item': types.ObjectType() }),
            codomain = types.Nothing)),
    ],
})
