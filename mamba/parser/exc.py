from mamba.lexer import SourceRange, Token


class ParseError(Exception):

    def __init__(self, source_range: SourceRange, message: str = ''):
        self.source_range = source_range
        self.message = message

    def __str__(self) -> str:
        if self.message:
            return f'{self.source_range.start}: {self.__class__.__name__}: {self.message}'
        else:
            return f'{self.source_range.start}: {self.__class__.__name__}'


class DuplicateKey(ParseError):

    def __init__(self, key: Token):
        super().__init__(operator.source_range, operator.value)
        self.key = key


class ImbalancedParenthesis(ParseError):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)


class UnexpectedToken(ParseError):

    def __init__(self, expected: str, got: Token, source_range: SourceRange):
        super().__init__(source_range, f"expected '{expected}', but got '{got}'")
        self.expected = expected
        self.got = got


class UnknownOperator(ParseError):

    def __init__(self, operator: Token):
        super().__init__(operator.source_range, operator.value)
        self.token = operator
