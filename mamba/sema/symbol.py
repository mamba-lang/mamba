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


builtin_scope = Scope(symbols={
    'Object': [Symbol(name='Object', type=types.TypeAlias(types.ObjectType()))],
    'Bool'  : [Symbol(name='Bool'  , type=types.TypeAlias(types.Bool))],
    'Int'   : [Symbol(name='Int'   , type=types.TypeAlias(types.Int))],
    'Float' : [Symbol(name='Float' , type=types.TypeAlias(types.Float))],
    'String': [Symbol(name='String', type=types.TypeAlias(types.String))],
    'List'  : [Symbol(name='List'  , type=types.TypeAlias(types.List))],
    'Set'   : [Symbol(name='Set'   , type=types.TypeAlias(types.Set))],
    'print' : [Symbol(name='print' , type=types.FunctionType(
        domain=types.ObjectType({ 'item': types.ObjectType() }), codomain=types.Nothing))],
})
