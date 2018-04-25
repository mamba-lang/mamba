from . import types


class Symbol(object):

    def __init__(self, name: str, type = None, overloadable: bool = False):
        self.name = name
        self.type = type
        self.overloadable = overloadable


class Scope(object):

    def __init__(self, parent = None, symbols = None):
        self.parent = parent
        self.symbols = set(symbols) if symbols is not None else set()

    def insert(self, symbol: Symbol):
        self.symbols.add(symbol)

    def contains(self, predicate: callable) -> bool:
        return self.first(where=predicate) is not None

    def first(self, where: callable) -> Symbol:
        for symbol in self.symbols:
            if where(symbol):
                return symbol
        return None


builtin_scope = Scope(symbols={
    Symbol(name='Object', type=types.TypeAlias(types.ObjectType())),
    Symbol(name='Bool'  , type=types.TypeAlias(types.Bool)),
    Symbol(name='Int'   , type=types.TypeAlias(types.Int)),
    Symbol(name='Float' , type=types.TypeAlias(types.Float)),
    Symbol(name='String', type=types.TypeAlias(types.String)),
    Symbol(name='List'),
    Symbol(name='Set'),
    Symbol(name='print'),
})
