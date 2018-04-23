from enum import Enum


class TokenKind(Enum):

    integer         = 'integer'
    float_          = 'float'
    string          = 'string'
    boolean         = 'bool'

    identifier      = 'identifier'
    operator        = 'operator'

    bind            = '='
    or_             = '|'
    dot             = '.'
    comma           = ','
    colon           = ':'
    semicolon       = ';'
    arrow           = '->'
    bold_arrow      = '=>'
    newline         = 'newline'
    eof             = 'eof'

    lparen          = '('
    rparen          = ')'
    lbrace          = '{'
    rbrace          = '}'
    lbracket        = '['
    rbracket        = ']'

    underscore      = '_'
    let             = 'let'
    func            = 'func'
    type            = 'type'
    infix           = 'infix'
    prefix          = 'prefix'
    postfix         = 'postfix'
    if_             = 'if'
    then            = 'then'
    else_           = 'else'
    match           = 'match'
    when            = 'when'
    for_            = 'for'
    in_             = 'in'
    while_          = 'while'
    continue_       = 'continue'
    break_          = 'break'
    do              = 'do'
    try_            = 'try'
    catch           = 'catch'

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