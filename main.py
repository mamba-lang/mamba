import sys

from contextlib import ContextDecorator

from mamba.lexer import Lexer
from mamba.parser import Parser
from mamba.parser.exc import ParseError

from mamba.sema.scope_builder import ScopeBuilder
from mamba.sema.scope_binder import ScopeBinder
from mamba.sema.constraint_inferer import ConstraintInferer
from mamba.sema.constraint_solver import ConstraintSolver


class indent(ContextDecorator):

    def __init__(self, spaces=2):
        self.spaces = spaces

    def __enter__(self):
        self.actual_print = globals().get('print', print)
        globals()['print'] = self.print
        return self

    def __exit__(self, type, value, traceback):
        globals()['print'] = self.actual_print
        return False

    def print(self, item='', **kwargs):
        output = '\n'.join(' ' * self.spaces + s for s in str(item).split('\n'))
        self.actual_print(output, **kwargs)



def print_error(error, filename):
    print(filename, end=':', file=sys.stderr)
    print(error, file=sys.stderr)

    start = error.source_range.start
    end = error.source_range.end
    with open(filename) as f:
        lines = f.readlines()

    print()
    print('  ' + lines[start.line - 1], end='', file=sys.stderr)
    print('  ' + ' ' * (start.column - 1), end='', file=sys.stderr)
    if (start.line == end.line) and (end.column - start.column > 1):
        print('~' * (end.column - start.column), file=sys.stderr)
    else:
        print('^', file=sys.stderr)
    print('', file=sys.stderr)


if __name__ == '__main__':
    filename = sys.argv[1]
    stream = list(Lexer(filename).lex())

    try:
        module = Parser(stream).parse()
    except ParseError as error:
        print_error(error, filename)
        exit(1)

    # Create the semantic passes.
    constraint_inferer = ConstraintInferer()
    passes = [
        ScopeBuilder(),      # Build the lexical scopes.
        ScopeBinder(),       # Bind identifiers to symbols.
        constraint_inferer,  # Infer the constraints of the type system.
    ]

    # Execute the semantic passes.
    for pass_ in passes:
        pass_.visit(module)
        for error in pass_.errors:
            print_error(error, filename)

    # Solve the type constraints.
    print('Constraint to solve:')
    print('--------------------')
    with indent():
        for c in constraint_inferer.constraints:
            print(c)
    print()

    print('Solutions:')
    print('----------')
    solver = ConstraintSolver(constraints=constraint_inferer.constraints)
    for i, solution in enumerate(solver):
        print(f'#{i + 1}:')
        if not isinstance(solution, Exception):
            with indent():
                for variable, ty in solution.items():
                    print(f'{variable}: {ty}')
        else:
            print_error(solution, filename)
