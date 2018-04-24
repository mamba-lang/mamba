from mamba import ast
from mamba.lexer import SourceLocation, SourceRange, Token, TokenKind

from . import exc


class Parser(object):

    def __init__(self, stream: list):
        self.stream = stream
        self.stream_position = 0

        self.infix_operators = {
            '||': { 'precedence': 10, 'associativity': 'left' },
            '&&': { 'precedence': 20, 'associativity': 'left' },
            '^' : { 'precedence': 30, 'associativity': 'left' },
            '==': { 'precedence': 40, 'associativity': 'left' },
            '!=': { 'precedence': 40, 'associativity': 'left' },
            '<' : { 'precedence': 50, 'associativity': 'left' },
            '<=': { 'precedence': 50, 'associativity': 'left' },
            '>' : { 'precedence': 50, 'associativity': 'left' },
            '>=': { 'precedence': 50, 'associativity': 'left' },
            '+' : { 'precedence': 60, 'associativity': 'left' },
            '-' : { 'precedence': 60, 'associativity': 'left' },
            '*' : { 'precedence': 70, 'associativity': 'left' },
            '/' : { 'precedence': 70, 'associativity': 'left' },
            '%' : { 'precedence': 70, 'associativity': 'left' },
            '**': { 'precedence': 80, 'associativity': 'right' },
            '.' : { 'precedence': 90, 'associativity': 'left' },
            '?' : { 'precedence': 90, 'associativity': 'left' },
            '!' : { 'precedence': 90, 'associativity': 'left' },
        }
        self.prefix_operators = { '+', '-' }
        self.postfix_operators = { '!', '?' }

    def peek(self) -> Token:
        return self.stream[self.stream_position]

    def consume(self, kind=None) -> Token:
        if self.stream_position >= len(self.stream):
            return None
        if (kind is not None) and self.stream[self.stream_position].kind != kind:
            return None

        self.stream_position += 1
        return self.stream[self.stream_position - 1]

    def consume_if(self, predicate: callable) -> Token:
        if self.stream_position >= len(self.stream):
            return None
        if not predicate(self.stream[self.stream_position]):
            return None
        return self.consume()

    def consume_newlines(self):
        for token in self.stream[self.stream_position:]:
            if token.kind != TokenKind.newline:
                return
            self.stream_position += 1

    def rewind_to(self, position: int):
        self.stream_position = position

    def unexpected_token(self, expected: str):
        token = self.peek()
        return exc.UnexpectedToken(expected=expected, got=token, source_range=token.source_range)

    def expected_identifier(self):
        return self.unexpected_token(expected='identifier')

    def attempt(self, parser: callable) -> ast.Node:
        backtrack = self.stream_position
        try:
            return parser()
        except:
            self.rewind_to(backtrack)
        return None

    def parse(self) -> ast.Node:
        declarations = []

        while True:
            # Skip statement delimiters.
            self.consume_newlines()

            # Check for eof.
            if self.peek().kind == TokenKind.eof:
                break

            # Parse a declaration.
            declarations.append(self.parse_declaration())

        if declarations:
            source_range = SourceRange(
                start=declarations[0].source_range.start, end=declarations[-1].source_range.end)
        else:
            source_range = SourceRange(start=SourceLocation())
        return ast.Module(declarations=declarations, source_range=source_range)

    def parse_sequence(self, delimiter: TokenKind, parse_item: callable) -> ast.Node:
        # Skip leading new lines.
        self.consume_newlines()

        # Parse as many elements as possible.
        elements = []
        while self.peek().kind != delimiter:
            elements.append(parse_item())

            # If the next consumable token isn't a separator, stop parsing items.
            self.consume_newlines()
            if self.consume(TokenKind.comma) is None:
                break
            # Skip trailing new lines after the separator.
            self.consume_newlines()

        return elements

    def parse_parenthesized(self, parser: callable) -> ast.ParenthesizedNode:
        start_token = self.consume(TokenKind.lparen)
        if start_token is None:
            raise self.unexpected_token(expected='(')

        self.consume_newlines()
        enclosed = parser()
        self.consume_newlines()
        end_token = self.consume(TokenKind.rparen)
        if end_token is None:
            raise exc.ImbalancedParenthesis(source_range=self.peek().source_range)

        return ast.ParenthesizedNode(
            node=enclosed,
            source_range=SourceRange(
                start=start_token.source_range.start, end=end_token.source_range.end))

    def parse_declaration(self) -> ast.Node:
        token = self.peek()
        if token.kind == TokenKind.func:
            return self.parse_function_declaration()
        elif token.kind == TokenKind.type:
            return self.parse_type_declaration()
        else:
            raise self.unexpected_token(expected='declaration')

    def parse_function_declaration(self) -> ast.FunctionDeclaration:
        # Parse the `func` keyword.
        start_token = self.consume(TokenKind.func)
        if start_token is None:
            raise self.unexpected_token(expected='func')

        # Parse the name of the function.
        name_token = self.consume(TokenKind.identifier)
        if name_token is None:
            raise self.expected_identifier()

        # Parse the domain of the function.
        self.consume_newlines()
        if self.peek().kind == TokenKind.underscore:
            domain = ast.Nothing(source_range=self.consume().source_range)
        else:
            # Attempt to parse an object property (i.e. the syntactic sugar for singletons).
            prop = self.attempt(self.parse_object_property)
            if prop is not None:
                domain = ast.ObjectType(members=[prop], source_range=prop.source_range)
            else:
                domain = self.parse_annotation()

        # Parse an arrow operator.
        self.consume_newlines()
        if self.consume(TokenKind.arrow) is None:
            raise self.unexpected_token(expected='->')

        # Parse the codomain of the function.
        self.consume_newlines()
        if self.peek().kind == TokenKind.underscore:
            codomain = ast.Nothing(source_range=self.consume().source_range)
        else:
            # Attempt to parse an object property (i.e. the syntactic sugar for singletons).
            prop = self.attempt(self.parse_object_property)
            if prop is not None:
                codomain = ast.ObjectType(members=[prop], source_range=prop.source_range)
            else:
                codomain = self.parse_annotation()

        # Parse the binding operator.
        self.consume_newlines()
        if self.consume(TokenKind.bind) is None:
            raise self.unexpected_token(expected='=')

        # Parse the body of the function.
        body = self.parse_expression()

        return ast.FunctionDeclaration(
            name=name_token.value,
            domain=domain,
            codomain=codomain,
            body=body,
            source_range=SourceRange(
                start=start_token.source_range.start, end=body.source_range.end))

    def parse_type_declaration(self) -> ast.TypeDeclaration:
        # Parse the `type` keyword.
        start_token = self.consume(TokenKind.type)
        if start_token is None:
            raise self.unexpected_token(expected='type')

        # Parse the name of the type.
        name_token = self.consume(TokenKind.identifier)
        if name_token is None:
            raise self.expected_identifier()

        # Parse the binding operator.
        self.consume_newlines()
        if self.consume(TokenKind.bind) is None:
            raise self.unexpected_token(expected='=')

        # Parse the body of the type.
        body = self.parse_union_type()

        return ast.TypeDeclaration(
            name=name_token.value,
            body=body,
            source_range=SourceRange(
                start=start_token.source_range.start, end=body.source_range.end))

    def parse_annotation(self) -> ast.Node:
        # Attempt to parse the special `_` annotation (i.e. absence thereof).
        if self.peek().kind == TokenKind.underscore:
            return ast.Nothing(source_range=self.consume().source_range)

        return self.parse_union_type()

    def parse_type(self) -> ast.Node:
        # Parse a parenthesized type.
        if self.peek().kind == TokenKind.lparen:
            return self.parse_parenthesized(self.parse_type)

        return self.attempt(self.parse_identifier) or self.parse_object_type()

    def parse_union_type(self) -> ast.Node:
        # If the current token is a left parenthesis, we can't already know whether it encloses a
        # single type of a union, or if it encloses the union type itself. In other words, are we
        # parsing `(T1 | T2)` or `(T1) | T2`?
        if self.peek().kind == TokenKind.lparen:
            # If parsing a parenthesized union type succeeds, then we use the result as the "first"
            # type of the union, in case the next consumable token is `|`. Otherwise, we retry
            # parsing the parenthesis as part of an individual.
            union = self.attempt(lambda: self.parse_parenthesized(self.parse_union_type))
            types = [union] if union is not None else [self.parse_type()]
        else:
            types = [self.parse_type()]

        # Attempt to parse other types, separated by `|`.
        while True:
            backtrack = self.stream_position
            self.consume_newlines()
            if self.consume(TokenKind.or_) is None:
                self.rewind_to(backtrack)
                break
            self.consume_newlines()
            types.append(self.parse_type())

        if len(types) > 1:
            return ast.UnionType(
                types=types,
                source_range=SourceRange(
                    start=types[0].source_range.start, end=types[-1].source_range.start))
        else:
            return types[0]

    def parse_object_type(self) -> ast.Node:
        # Parse a left brace.
        start_token = self.consume(TokenKind.lbrace)
        if start_token is None:
            raise self.unexpected_token(expected='{')

        # Parse the key/value pairs of the type.
        members = self.parse_sequence(TokenKind.rbrace, self.parse_object_property)
        end_token = self.consume(TokenKind.rbrace)
        if end_token is None:
            raise self.unexpected_token(expected='}')

        return ast.ObjectType(
            members=members,
            source_range=SourceRange(
                start=start_token.source_range.start, end=end_token.source_range.end))

    def parse_object_property(self) -> ast.Node:
        # Parse the name of the property.
        name_token = self.consume()
        if (name_token is None) or (name_token.kind != TokenKind.identifier):
            raise self.expected_identifier()
        name = name_token.value

        # Parse the optional annotation of the property.
        backtrack = self.stream_position
        self.consume_newlines()
        if self.consume(TokenKind.colon) is not None:
            annotation = self.parse_annotation()
            end = annotation.source_range.end
        else:
            self.rewind_to(backtrack)
            annotation = None
            end = name_token.source_range.end

        return ast.ObjectProperty(
            name=name, annotation=annotation,
            source_range=SourceRange(start=name_token.source_range.start, end=end))

    def parse_expression(self) -> ast.Node:
        # Attempt to parse a binding.
        if self.peek().kind == TokenKind.let:
            return self.parse_binding()

        # Attempt to parse a term.
        left = self.attempt(self.parse_closure_expression) or self.parse_atom()

        # Attempt to parse the remainder of an infix expression.
        while True:
            backtrack = self.stream_position
            self.consume_newlines()
            operator = self.consume(TokenKind.operator)
            if operator is None:
                self.rewind_to(backtrack)
                break
            if operator.value not in self.infix_operators:
                raise exc.UnknownOperator(operator=operator)

            # Parse the right operand.
            right = self.parse_atom()

            # If the left operand is an infix expression, we should check the precedence and
            # associativity of its operator against the current one.
            if isinstance(left, ast.InfixExpression):
                lprec = self.infix_operators[left.operator.value]['precedence']
                rprec = self.infix_operators[operator.value]['precedence']
                associativity = self.infix_operators[left.operator.value]['associativity']

                if ((lprec < rprec) or
                    ((left.operator.value == operator.value) and (associativity == 'right'))):

                    new_right = ast.InfixExpression(
                        operator=operator, left=left.right, right=right,
                        source_range=SourceRange(
                            start=left.right.source_range.start, end=right.source_range.end))
                    left = ast.InfixExpression(
                        operator=left.operator, left=left.left, right=new_right,
                        source_range=SourceRange(
                            start=left.left.source_range.start, end=right.source_range.end))
                    continue


            left = ast.InfixExpression(
                operator=operator, left=left, right=right,
                source_range=SourceRange(
                    start=left.source_range.start, end=right.source_range.end))
            continue

        return left

    def parse_binding(self) -> ast.Binding:
        start_token = self.consume(TokenKind.let)
        if start_token is None:
            raise self.unexpected_token(expected='let')

        # Parse the name of the binding.
        self.consume_newlines()
        name_token = self.consume(TokenKind.identifier)
        if name_token is None:
            raise self.expected_identifier()

        # Parse the optional annotation of the binding.
        backtrack = self.stream_position
        self.consume_newlines()
        if self.consume(TokenKind.colon) is not None:
            annotation = self.parse_annotation()
            end = annotation.source_range.end
        else:
            self.rewind_to(backtrack)
            annotation = None
            end = name_token.source_range.end

        return ast.Binding(
            name=name_token.value, annotation=annotation,
            source_range=SourceRange(start=start_token.source_range.start, end=end))

    def parse_atom(self) -> ast.Node:
        start_token = self.peek()

        if start_token.kind == TokenKind.lparen:
            atom = self.parse_parenthesized(self.parse_expression)

        elif start_token.kind in scalar_literal_kinds:
            token = self.consume()
            atom = ast.ScalarLiteral(value=token.value, source_range=token.source_range)
        elif start_token.kind == TokenKind.identifier:
            atom = self.parse_identifier()
        elif start_token.kind == TokenKind.lbracket:
            atom = self.parse_list_literal()
        elif start_token.kind == TokenKind.lbrace:
            atom = self.parse_object_literal()
        elif start_token.kind == TokenKind.if_:
            atom = self.parse_if_expression()
        elif start_token.kind == TokenKind.match:
            atom = self.parse_match_expression()
        elif (start_token.kind == TokenKind.operator) and (start_token.value in self.prefix_operators):
            atom = self.parse_prefix_expression()
        else:
            raise self.unexpected_token(expected='expression')

        # Parse the optional "suffix" of the expression.
        while True:
            backtrack = self.stream_position
            self.consume_newlines()

            # If we can parse an object, we interpret it as a call expression.
            try:
                argument = self.attempt(self.parse_object_literal)
                if argument is None:
                    value = self.parse_expression()

                    # Operators that can act as both an infix and a prefix or postfix operator
                    # introduce some ambuiguity, as to how an expression like `a + b` should be
                    # parsed. The most intuitive way to interpret this expression is arguably to
                    # see `+` as an infix operator, but one may also see this as the application of
                    # `a` to the expression `+b` (i.e. `a { _0 = +b }`), or the application of `a+`
                    # the expression `b` (i.e. `a+ { _0 = b }`).
                    # We choose to desambiguise this situation by prioritizing infix expressions.
                    if isinstance(value, ast.PrefixExpression):
                        if value.operator.value in self.infix_operators:
                            self.rewind_to(backtrack)
                            break

                    argument = ast.ObjectLiteral(
                        items={ '_0': value }, source_range=value.source_range)

                atom = ast.CallExpression(
                    callee=atom,
                    argument=argument,
                    source_range=SourceRange(
                        start=atom.source_range.start, end=argument.source_range.end))
                continue

            except:
                self.rewind_to(backtrack)
                self.consume_newlines()

            suffix_token = self.peek()

            # An underscore corresponds to a call to a function without any argument.
            if suffix_token == TokenKind.underscore:
                end_token = self.consume()
                atom = ast.CallExpression(
                    callee=atom,
                    argument=None,
                    source_range=SourceRange(
                        start=atom.source_range.start, end=end_token.source_range.end))
                continue

            # If we can parse a postfix operator, we interpret it as a postfix expression.
            if suffix_token.kind == TokenKind.operator and (suffix_token.value in self.postfix_operators):
                operator = self.consume()

                # Backtrack if the operator is also infix and the remainder of the stream can be
                # parsed as an expression.
                if operator.value in self.infix_operators:
                    if self.attempt(self.parse_expression) is not None:
                        self.rewind_to(backtrack)
                        break

                atom = ast.PostfixExpression(
                    operator=operator,
                    operand=atom,
                    source_range=SourceRange(
                        start=operator.source_range.start, end=atom.source_range.end))
                continue

            self.rewind_to(backtrack)
            break

        return atom

    def parse_prefix_expression(self) -> ast.PrefixExpression:
        # Parse the operator of the expression.
        start_token = self.consume()
        if (start_token is None) or (start_token.value not in self.prefix_operators):
            raise self.unexpected_token(expected='prefix operator')

        # Parse the operand of the expression.
        operand = self.parse_expression()
        return ast.PrefixExpression(
            operator=start_token, operand=operand,
            source_range=SourceRange(
                start=start_token.source_range.start, end=operand.source_range.end))

    def parse_closure_expression(self) -> ast.ClosureExpression:
        start_token = self.peek()

        # Parse the domain definition.
        if start_token.kind == TokenKind.underscore:
            self.consume()
            domain = ast.Nothing(source_range=self.consume().source_range)
        else:
            # Attempt to parse an object property (i.e. the syntactic sugar for singletons).
            prop = self.attempt(self.parse_object_property)
            if prop is not None:
                domain = ast.ObjectType(members=[prop], source_range=prop.source_range)
            else:
                domain = self.parse_annotation()

        # Parse the optional codomain.
        self.consume_newlines()
        if self.consume(TokenKind.arrow) is not None:
            self.consume_newlines()
            if self.peek().kind == TokenKind.underscore:
                codomain = ast.Nothing(source_range=self.consume().source_range)
            else:
                # Attempt to parse an object property (i.e. the syntactic sugar for singletons).
                prop = self.attempt(self.parse_object_property)
                if prop is not None:
                    codomain = ast.ObjectType(members=[prop], source_range=prop.source_range)
                else:
                    codomain = self.parse_annotation()
        else:
            codomain = None

        # Parse the bold arrow operator.
        self.consume_newlines()
        if self.consume(TokenKind.bold_arrow) is None:
            raise self.unexpected_token(expected='=>')

        # Parse the body of the function.
        body = self.parse_expression()

        return ast.ClosureExpression(
            domain=domain,
            codomain=codomain,
            body=body,
            source_range=SourceRange(
                start=start_token.source_range.start, end=body.source_range.end))

    def parse_if_expression(self) -> ast.IfExpression:
        # Parse the `if` keyword.
        if_token = self.consume(TokenKind.if_)
        if if_token is None:
            raise self.unexpected_token(expected='if')

        # Parse the condition of the expression.
        self.consume_newlines()
        condition = self.parse_expression()

        # Parse the `then` keyword.
        self.consume_newlines()
        if self.consume(TokenKind.then) is None:
            raise self.unexpected_token(expected='then')

        # Parse the "then" expression.
        self.consume_newlines()
        then = self.parse_expression()

        # Parse the `else` keyword.
        self.consume_newlines()
        if self.consume(TokenKind.else_) is None:
            raise self.unexpected_token(expected='else')

        # Parse the "then" expression.
        self.consume_newlines()
        else_ = self.parse_expression()

        return ast.IfExpression(
            condition=condition, then=then, else_=else_,
            source_range=SourceRange(
                start=if_token.source_range.start, end=else_.source_range.end))

    def parse_match_expression(self) -> ast.MatchExpression:
        start_token = self.consume(TokenKind.match)
        if start_token is None:
            raise self.unexpected_token(expected='match')

        # Parse the subject.
        self.consume_newlines()
        subject = self.parse_expression()

        # Parse the different cases.
        self.consume_newlines()
        case_token = self.peek()
        cases = []
        while case_token.kind in { TokenKind.when, TokenKind.else_ }:
            cases.append(self.parse_match_case())
            self.consume_newlines()
            case_token = self.peek()

        if not cases:
            raise exc.ParseError(
                message='match expressions should have at least one case',
                source_range=self.peek().source_range)

        return ast.MatchExpression(
            subject=subject, cases=cases,
            source_range=SourceRange(
                start=start_token.source_range.start, end=cases[-1].source_range.end))

    def parse_match_case(self) -> ast.Node:
        start_token = self.peek()

        # Parse a when case.
        if start_token.kind == TokenKind.when:
            # Parse the case pattern.
            self.consume()
            self.consume_newlines()
            pattern = self.parse_expression()

            # Parse the `then` keyword.
            self.consume_newlines()
            if self.consume(TokenKind.then) is None:
                raise self.unexpected_token(expected='then')

            # Parse the case body.
            self.consume_newlines()
            body = self.parse_expression()

            return ast.WhenCase(
                pattern=pattern, body=body,
                source_range=SourceRange(
                    start=start_token.source_range.start, end= body.source_range.end))

        # Parse an else case.
        if start_token.kind == TokenKind.else_:
            # Parse the case body.
            self.consume()
            self.consume_newlines()
            body = self.parse_expression()

            return ast.ElseCase(
                body=body,
                source_range=SourceRange(
                    start=start_token.source_range.start, end=body.source_range.end))

        raise self.unexpected_token(expected='when')

    def parse_identifier(self) -> ast.Node:
        # Parse the identifier's name.
        identifier_token = self.consume(TokenKind.identifier)
        if identifier_token is None:
            raise self.expected_identifier()

        # Parse the optional specializers.
        def parse_name():
            name = self.consume(TokenKind.identifier)
            if name is None:
                raise self.expected_identifier()
            return name.value

        backtrack = self.stream_position
        self.consume_newlines()
        if self.consume(TokenKind.lbracket):
            specializers = self.parse_sequence(TokenKind.rbracket, parse_name)
            end_token = self.consume(TokenKind.rbracket)
            if end_token is None:
                raise self.unexpected_token(expected=']')
            end = end_token.source_range.end
        else:
            self.rewind_to(backtrack)
            specializers = None
            end = identifier_token.source_range.end

        return ast.Identifier(
            name=identifier_token.value,
            specializers=specializers,
            source_range=SourceRange(start=identifier_token.source_range.start, end=end))

    def parse_scalar_literal(self) -> ast.ScalarLiteral:
        if self.peek().kind in { TokenKind.boolean, TokenKind.number, TokenKind.string }:
            token = self.consume()
            return ast.ScalarLiteral(value=token.value, source_range=token.source_range)
        else:
            raise self.unexpected_token(expected='literal value')

    def parse_list_literal(self) -> ast.ListLiteral:
        # Parse a left bracket.
        start_token = self.consume(TokenKind.lbracket)
        if start_token is None:
            raise self.unexpected_token(expected='[')

        # Parse the items of the list.
        items = self.parse_sequence(TokenKind.rbracket, self.parse_expression)
        end_token = self.consume(TokenKind.rbracket)
        if end_token is None:
            raise self.unexpected_token(expected=']')

        return ast.ListLiteral(
            items=items,
            source_range=SourceRange(
                start=start_token.source_range.start, end=end_token.source_range.end))

    def parse_object_literal(self) -> ast.ObjectLiteral:
        # Parse a left brace.
        start_token = self.consume(TokenKind.lbrace)
        if start_token is None:
            raise self.unexpected_token(expected='{')

        # Parse the items of the object.
        items = self.parse_sequence(TokenKind.rbrace, self.parse_object_literal_item)
        end_token = self.consume(TokenKind.rbrace)
        if end_token is None:
            raise self.unexpected_token(expected='}')

        return ast.ObjectLiteral(
            items={ key: value for key, value in items },
            source_range=SourceRange(
                start=start_token.source_range.start, end=end_token.source_range.end))

    def parse_object_literal_item(self) -> tuple:
        # Parse the name of the item.
        name_token = self.consume()
        if (name_token is None) or (name_token.kind != TokenKind.identifier):
            raise self.expected_identifier()
        name = name_token.value

        # Parse the binding operator.
        self.consume_newlines()
        if self.consume(TokenKind.bind) is None:
            raise self.unexpected_token(expected='=')

        # Parse the value of the item.
        value = self.parse_expression()
        return (name, value)


scalar_literal_kinds = {
    TokenKind.boolean,
    TokenKind.integer,
    TokenKind.float_,
    TokenKind.string
}
