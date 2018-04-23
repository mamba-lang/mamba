from mamba.lexer import SourceRange


class ParseError(Exception):

    def __init__(self, source_range: SourceRange, message: str = ''):
        self.source_range = source_range
        self.message = message


class ExpectedIdentifier(ParseError):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)


class ExpectedAnnotation(ParseError):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)


class ExpectedDeclaration(ParseError):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)


class UnexpectedToken(ParseError):

    def __init__(self, expected: str, source_range: SourceRange):
        super().__init__(source_range)
        self.expected = expected


class ImbalancedParenthesis(ParseError):

    def __init__(self, source_range: SourceRange):
        super().__init__(source_range)
