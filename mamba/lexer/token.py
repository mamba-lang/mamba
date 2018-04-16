from enum import Enum


class TokenKind(Enum):

    integer         = 'integer'
    float_          = 'float'
    string          = 'string'
    boolean         = 'bool'

    identifier      = 'identifier'

    pow_            = '**'
    mul             = '*'
    matmul          = '@'
    truediv         = '/'
    floordiv        = '//'
    mod             = '%'
    add             = '+'
    sub             = '-'
    lshift          = '<<'
    rshift          = '>>'
    lt              = '<'
    le              = '<='
    ge              = '>='
    gt              = '>'
    in_             = 'in'
    eq              = '=='
    ne              = '!='
    is_             = 'is'
    invert          = '~'
    and_            = '&'
    xor             = '^'
    or_             = '|'
    land            = 'and'
    lor             = 'or'
    lnot            = 'not'
    assign          = '='
    arrow           = '->'

    dot             = '.'
    comma           = ','
    colon           = ':'
    semicolon       = ';'
    newline         = 'newline'
    eof             = 'eof'

    lparen          = '('
    rparen          = ')'
    lbrace          = '{'
    rbrace          = '}'
    lbracket        = '['
    rbracket        = ']'

    let             = 'let'
    def_            = 'def'

    unterminated_string_literal = 'unterminated_string_literal'
    unknown = 'unknown'


class Token(object):

    def __init__(self, kind, source_range, value=None):
        self.kind = kind
        self.source_range = source_range
        self.value = value

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.value is not None:
            return f'<{self.kind} {self.value}>'
        else:
            return f'<{self.kind}>'
