from mamba.lexer.token import Token, TokenKind


class SourceLocation(object):

    def __init__(self, line: int = 1, column: int = 1, offset: int = 0):
        self.line = line
        self.column = column
        self.offset = offset


class SourceRange(object):

    def __init__(self, start: SourceLocation, end: SourceLocation=None):
        self.start = start
        self.end = end or start


class Lexer(object):

    def __init__(self, filename: str):
        self.filename = filename
        with open(filename) as f:
            self.characters = f.read()

        self.char_index = 0
        self.location = SourceLocation()

    def take(self, n: int = 1) -> str:
        start_index = self.char_index
        for i in range(n):
            char = self.current_char
            if char is None:
                return self.characters[start_index : self.char_index]
            elif char == '\n':
                self.location.line += 1
                self.location.column = 1
            else:
                self.location.column += 1
            self.location.offset += 1
            self.char_index += 1
        return self.characters[start_index : self.char_index]

    def take_while(self, predicate: callable) -> str:
        start_index = self.char_index
        while (self.current_char is not None) and predicate(self.current_char):
            self.take()
        return self.characters[start_index : self.char_index]

    def skip(self, n: int = 1):
        self.take(n)

    def skip_while(self, predicate: callable) -> str:
        while (self.current_char is not None) and predicate(self.current_char):
            self.take()

    def char(self, index: int):
        forward_index = self.char_index + index
        if forward_index < len(self.characters):
            return self.characters[forward_index]
        else:
            return None

    @property
    def current_char(self):
        if self.char_index < len(self.characters):
            return self.characters[self.char_index]
        else:
            return None

    def lex(self):
        while True:
            # Ignore whitespaces.
            self.skip_while(is_whitespace)

            # Check for the end of file.
            char = self.current_char
            if char is None:
                yield Token(kind=TokenKind.eof, source_range=SourceRange(start=self.location))
                return

            # Check for statement delimiters.
            if is_statement_delimiter(char):
                kind = TokenKind.newline if char == '\n' else TokenKind.semicolon
                token = Token(kind=kind, source_range=SourceRange(start=self.location))
                self.skip_while(lambda c: c.isspace() or is_statement_delimiter(c))
                yield token
                continue

            # Ignore comments.
            if char == '#':
                self.skip_while(lambda c: c != '\n')
                continue

            start = self.location

            # Check for number literals.
            if char.isdigit():
                number = self.take_while(str.isdigit)
                kind = TokenKind.integer
                if self.current_char == '.':
                    self.skip()
                    fraction = self.take_while(str.isdigit)
                    number += '.' + fraction
                    kind = TokenKind.float_
                    value = float(number)
                else:
                    value = int(number)
                yield Token(
                    kind=kind,
                    source_range=SourceRange(start=start, end=self.location),
                    value=value)
                continue

            # Check for identifiers.
            if is_alnum_or_underscore(char):
                string = self.take_while(is_alnum_or_underscore)
                source_range = SourceRange(start=start, end=self.location)
                if string in { 'true', 'false' }:
                    value = string == 'true'
                    yield Token(kind=TokenKind.boolean, source_range=source_range, value=value)
                elif string in reserved_keywords:
                    yield Token(kind=reserved_keywords[string], source_range=source_range)
                else:
                    yield Token(kind=TokenKind.identifier, source_range=source_range, value=string)
                continue

            # Check for string literals.
            if (char == "'") or (char == '"'):
                self.skip()
                start_index = self.char_index
                while self.current_char != char:
                    # Check for unterminated string literals.
                    if self.char_index >= len(self.characters):
                        self.skip_while(lambda _: True)
                        yield Token(
                            kind=TokenKind.unterminated_string_literal,
                            source_range=SourceRange(start=start, end=self.location))
                        return
                    self.skip()

                    # Skip escaped end quotes.
                    if (self.current_char == '\\') and (self.char(1) == char):
                        self.skip(2)

                value = self.characters[start_index : self.char_index]
                self.skip()
                yield Token(
                    kind=TokenKind.string,
                    source_range=SourceRange(start=start, end=self.location),
                    value=value)
                continue

            # Check for operators.
            if is_operator(char):
                # Check for reserved operators.
                if char in reserved_operators:
                    self.skip()
                    source_range = SourceRange(start=start, end=self.location)
                    yield Token(kind=reserved_operators[char], source_range=source_range)
                    continue

                # Build other operators.
                op = char + self.take_while(is_operator)
                source_range = SourceRange(start=start, end=self.location)
                yield Token(kind=TokenKind.operator, source_range=source_range, value=op)
                continue

            self.skip()
            yield Token(
                kind=TokenKind.unknown,
                source_range=SourceRange(start=start, end=self.location),
                value=char)


def is_whitespace(char: str) -> bool:
    return char in { ' ', '\t' }


def is_statement_delimiter(char: str) -> bool:
    return char in { '\n', ';' }


def is_alnum_or_underscore(char: str) -> bool:
    return (char == '_') or char.isalnum() or char.isdigit()


def is_operator(char: str) -> bool:
    return char in '*@/%+-<>=!~&^|.,:;({[]})'


reserved_keywords = {
    'let'      : TokenKind.let,
    'func'     : TokenKind.func,
    'type'     : TokenKind.type,
    'infix'    : TokenKind.infix,
    'prefix'   : TokenKind.prefix,
    'postfix'  : TokenKind.postfix,
    'if'       : TokenKind.if_,
    'then'     : TokenKind.then,
    'else'     : TokenKind.else_,
    'match'    : TokenKind.match,
    'when'     : TokenKind.when,
    'for'      : TokenKind.for_,
    'in'       : TokenKind.in_,
    'while'    : TokenKind.while_,
    'continue' : TokenKind.continue_,
    'break'    : TokenKind.break_,
    'do'       : TokenKind.do,
    'try'      : TokenKind.try_,
    'catch'    : TokenKind.catch,
}


reserved_operators = {
    '=': TokenKind.bind,
    '|': TokenKind.or_,
    '.': TokenKind.dot,
    ',': TokenKind.comma,
    ';': TokenKind.semicolon,
    ':': TokenKind.colon,
    '(': TokenKind.lparen,
    ')': TokenKind.rparen,
    '{': TokenKind.lbrace,
    '}': TokenKind.rbrace,
    '[': TokenKind.lbracket,
    ']': TokenKind.rbracket
}
