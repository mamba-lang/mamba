from mamba.lexer import SourceRange


class SemanticError(Exception):

    def __init__(self, source_range: SourceRange, message: str = ''):
        self.source_range = source_range
        self.message = message

    def __str__(self) -> str:
        if self.message:
            return f'{self.source_range.start}: {self.__class__.__name__}: {self.message}'
        else:
            return f'{self.source_range.start}: {self.__class__.__name__}'


class DuplicateDeclaration(SemanticError):

    def __init__(self, name: str, source_range: SourceRange):
        super().__init__(source_range, name)
        self.name = name


class UnboundName(SemanticError):

    def __init__(self, name: str, source_range: SourceRange):
        super().__init__(source_range, name)
        self.name = name


class UnificationError(SemanticError):

    def __init__(self, lhs, rhs, message: str, source_range: SourceRange):
        super().__init__(source_range, message)
        self.lhs = lhs
        self.rhs = rhs
