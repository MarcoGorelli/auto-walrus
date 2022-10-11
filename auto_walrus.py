from __future__ import annotations

import argparse
import ast
import sys
from typing import Sequence
from typing import Tuple

SEP_SYMBOLS = frozenset(('(', ')', ',', ':'))
# name, lineno, col_offset, end_lineno, end_col_offset
Token = Tuple[str, int, int, int, int]

COMMENT = '# no-walrus'
SIMPLE_NODE = (ast.Name, ast.Constant)


def name_lineno_col_offset_list(
        tokens: list[Token],
) -> list[tuple[str, int, int]]:
    return [(token[0], token[1], token[2]) for token in tokens]


def name_lineno_col_offset(tokens: Token) -> tuple[str, int, int]:
    return tokens[0], tokens[1], tokens[2]


def record_name_lineno_col_offset(
        node: ast.Name,
        end_lineno: int | None = None,
        end_col_offset: int | None = None,
) -> Token:
    if end_lineno is None:
        assert node.end_lineno is not None
        _end_lineno = node.end_lineno
    else:
        _end_lineno = end_lineno
    if end_col_offset is None:
        assert node.end_col_offset is not None
        _end_col_offset = node.end_col_offset
    else:
        _end_col_offset = end_col_offset
    return (
        node.id,
        node.lineno,
        node.col_offset,
        _end_lineno,
        _end_col_offset,
    )


def find_names(
        node: ast.AST,
        end_lineno: int | None = None,
        end_col_offset: int | None = None,
) -> set[Token]:
    names = set()
    for _node in ast.walk(node):
        if isinstance(_node, ast.Name):
            names.add(
                record_name_lineno_col_offset(
                    _node, end_lineno, end_col_offset,
                ),
            )
    return names


def is_simple_test(node: ast.AST) -> bool:
    # TODO: this is definitely covered, if
    # I run tests and put a breakpoint here then it
    # gets here, and returns both True and False.
    # So why is it reported as uncovered?
    return (  # pragma: no cover
        isinstance(node, SIMPLE_NODE)
        or (
            isinstance(node, ast.Compare)
            and isinstance(node.left, SIMPLE_NODE)
            and (
                all(
                    isinstance(_node, SIMPLE_NODE)
                    for _node in node.comparators
                )
            )
        )
    )


def visit_function_def(
    node: ast.FunctionDef | ast.Module,
    path: str,
) -> list[tuple[Token, Token]]:
    names: set[Token] = set()
    assignments: set[Token] = set()
    ifs: set[Token] = set()
    related_vars: dict[str, list[Token]] = {}

    _set_names(names, node)

    _set_ast_expression_types(assignments, ifs, node, related_vars)

    sorted_assignments, sorted_ifs, \
        sorted_names = _get_sorted_names_assignments_ifs(
            assignments, ifs, names,
        )
    walrus = []

    for _assignment in sorted_assignments:
        _if_statements = [i for i in sorted_ifs if i[0] == _assignment[0]]
        if len(_if_statements) != 1:
            continue
        _if_statement = _if_statements[0]
        assignment_idx = _get_assignment_index(_assignment, sorted_names)
        if_statement_idx = _get_if_statement_index(_if_statement, sorted_names)
        _other_assignments = _get_other_assignments(
            _assignment, sorted_assignments,
        )
        _other_usages = _get_other_usages(_assignment, sorted_names)
        if (
                _is_name_appears_between_assignment_and_if(
                    _assignment, assignment_idx,
                    if_statement_idx, sorted_names,
                )
                and _is_variable_only_assignment(_other_assignments)
                and _is_name_used_first_time(_assignment, _other_usages)
                and _is_name_used_elsewhere(_other_usages)
        ):

            related = related_vars[_assignment[0]]
            should_break = False
            should_break = _is_right_side_name_used_between_assignment_and_if(
                assignment_idx, if_statement_idx, related,
                should_break, sorted_names,
            )
            if should_break:
                continue
            walrus.append((_assignment, _if_statement))
    return walrus


def _get_sorted_names_assignments_ifs(
    assignments: set[Token],
    ifs: set[Token],
    names: set[Token],
) -> tuple[list[Token], list[Token], list[Token]]:
    sorted_names = sorted(names, key=lambda x: (x[1], x[2]))
    sorted_assignments = sorted(assignments, key=lambda x: (x[1], x[2]))
    sorted_ifs = sorted(ifs, key=lambda x: (x[1], x[2]))
    return sorted_assignments, sorted_ifs, sorted_names


def _get_other_usages(
    _assignment: Token,
    sorted_names: list[Token],
) -> list[tuple[str, int, int]]:
    return [
        name_lineno_col_offset(
            name,
        ) for name in sorted_names if name[0] == _assignment[0]
    ]


def _get_other_assignments(
    _assignment: Token,
    sorted_assignments: list[Token],
) -> list[tuple[str, int, int]]:
    return [
        name_lineno_col_offset(assignment)
        for assignment in sorted_assignments if assignment[0] == _assignment[0]
    ]


def _get_if_statement_index(
    _if_statement: Token,
    sorted_names: list[Token],
) -> int:
    return name_lineno_col_offset_list(
        sorted_names,
    ).index(name_lineno_col_offset(_if_statement))


def _get_assignment_index(
    _assignment: Token,
    sorted_names: list[Token],
) -> int:
    return name_lineno_col_offset_list(
        sorted_names,
    ).index(name_lineno_col_offset(_assignment))


def _is_right_side_name_used_between_assignment_and_if(
    assignment_idx: int,
    if_statement_idx: int,
    related: list[Token],
    should_break: bool,
    sorted_names: list[Token],
) -> bool:
    # Check that names which appear in right hand side of
    # assignment aren't used between assignment and if-statement.
    for rel in related:
        usages = [
            name for name in sorted_names if name[0] == rel[0] if name != rel
        ]
        for usage in usages:
            rel_used_idx = name_lineno_col_offset_list(
                sorted_names,
            ).index(name_lineno_col_offset(usage))
            if assignment_idx < rel_used_idx < if_statement_idx:
                should_break = True
    return should_break


def _is_name_appears_between_assignment_and_if(
    _assignment: Token,
    assignment_idx: int,
    if_statement_idx: int,
    sorted_names: list[Token],
) -> bool:
    # check name doesn't appear between assignment and if statement
    return _assignment[0] not in [
        sorted_names[i][0]
        for i in range(assignment_idx + 1, if_statement_idx)
    ]


def _is_name_used_elsewhere(_other_usages: list[tuple[str, int, int]]) -> bool:
    # check it's used at least somewhere else
    return len(_other_usages) > 2


def _is_name_used_first_time(
    _assignment: Token,
    _other_usages: list[tuple[str, int, int]],
) -> bool:
    # check this is the first usage of this name
    return _other_usages[0] == name_lineno_col_offset(_assignment)


def _is_variable_only_assignment(
    _other_assignments: list[tuple[str, int, int]],

) -> bool:
    # check it's the variable's only assignment
    return len(_other_assignments) == 1


def _set_ast_expression_types(
    assignments: set[Token],
    ifs: set[Token],
    node: ast.AST,
    related_vars: dict[str, list[Token]],
) -> None:
    for _node in node.body:  # type: ignore
        if isinstance(_node, ast.Assign):
            if (
                    len(_node.targets) == 1
                    and isinstance(_node.targets[0], ast.Name)
            ):
                target = _node.targets[0]
                assignments.add(
                    record_name_lineno_col_offset(
                        target, _node.end_lineno, _node.end_col_offset,
                    ),
                )
                related_vars[target.id] = list(find_names(_node.value))
        elif isinstance(_node, ast.If) and is_simple_test(_node.test):
            ifs.update(find_names(_node.test))
            for __node in _node.orelse:
                if isinstance(__node, ast.If) and is_simple_test(__node.test):
                    ifs.update(
                        find_names(
                            __node.test,
                        ),
                    )
        elif (
            isinstance(_node, (ast.If, ast.While))
            and is_simple_test(_node.test)
        ):
            ifs.update(find_names(_node.test))


def _set_names(names: set[Token], node: ast.AST) -> None:
    for _node in ast.walk(node):
        names.update(find_names(_node))


def auto_walrus(content: str, path: str, line_length: int) -> str | None:
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:  # pragma: no cover
        return None

    walruses = _get_sorted_walruses(path, tree)

    if not walruses:
        return None

    lines_to_remove: list[str] = []
    _add_walruses(line_length, lines, lines_to_remove, walruses)

    new_content = _get_new_content(lines, lines_to_remove)
    new_content = _add_new_line(content, new_content)
    return new_content if new_content != content else None


def _add_walruses(
    line_length: int,
    lines: list[str],
    lines_to_remove: list[str],
    walruses: list[tuple[Token, Token]],
) -> None:
    for _assignment, _if_statement in walruses:
        if _assignment[1] != _assignment[3]:
            continue
        txt = lines[_assignment[1] - 1][_assignment[2]:_assignment[4]]
        if txt.count('=') > 1:
            continue
        left_bit, right_bit = _get_left_and_right_bits(_if_statement, lines)
        no_paren = _is_no_paren(left_bit, right_bit)
        line_with_walrus = _get_line_with_walrus(
            left_bit, no_paren, right_bit, txt,
        )
        if len(line_with_walrus) > line_length:
            # don't rewrite if it would split over multiple lines
            continue
        # replace assignment
        line_without_assignment = (
            f'{lines[_assignment[1]-1][:_assignment[2]]}'
            f'{lines[_assignment[1]-1][_assignment[4]:]}'
        )
        if (
            COMMENT in lines[_assignment[1]-1]
        ) or (
            COMMENT in lines[_if_statement[1]-1]
        ):
            continue
        lines[_assignment[1] - 1] = line_without_assignment

        _add_walrus(_if_statement, line_with_walrus, lines)
        _remove_empty_line(_assignment, lines, lines_to_remove)


def _is_no_paren(left_bit: str, right_bit: str) -> bool:
    return any(left_bit.endswith(i) for i in SEP_SYMBOLS) \
        and any(right_bit.startswith(i) for i in SEP_SYMBOLS)


def _get_left_and_right_bits(
    _if_statement: Token, lines: list[str],
) -> tuple[str, str]:
    line = lines[_if_statement[1] - 1]
    left_bit = line[:_if_statement[2]]
    right_bit = line[_if_statement[4]:]
    return left_bit, right_bit


def _get_line_with_walrus(
    left_bit: str,
    no_paren: bool,
    right_bit: str,
    txt: str,
) -> str:
    replace = txt.replace('=', ':=')
    line_with_walrus = f'{left_bit}({replace}){right_bit}'
    if no_paren:
        line_with_walrus = left_bit + replace + right_bit

    return line_with_walrus


def _add_new_line(content: str, new_content: str) -> str:
    if new_content and content.endswith('\n'):
        new_content += '\n'
    return new_content


def _get_new_content(lines: list[str], lines_to_remove: list[str]) -> str:
    newlines = [
        line for i, line in enumerate(
            lines,
        ) if i not in lines_to_remove
    ]
    return '\n'.join(newlines)


def _remove_empty_line(
    _assignment: Token,
    lines: list[str],
    lines_to_remove: list[str],
) -> None:
    # remove empty line
    if not lines[_assignment[1] - 1].strip():
        lines_to_remove.append(_assignment[1] - 1)  # type: ignore


def _add_walrus(
    _if_statement: Token,
    line_with_walrus: str,
    lines: list[str],
) -> None:
    # add walrus
    lines[_if_statement[1] - 1] = line_with_walrus


def _replace_assignment(_assignment: Token, lines: list[str]) -> None:
    # replace assignment
    line_without_assignment = (
        f'{lines[_assignment[1] - 1][:_assignment[2]]}'
        f'{lines[_assignment[1] - 1][_assignment[4]:]}'
    )
    lines[_assignment[1] - 1] = line_without_assignment


def _get_sorted_walruses(
    path: str, tree: ast.AST,
) -> list[tuple[Token, Token]]:
    walruses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            walruses.extend(visit_function_def(node, path))
    walruses = sorted(walruses, key=lambda x: (-x[1][1], -x[1][2]))
    return walruses


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    # black formatter's default
    parser.add_argument('--line-length', type=int, default=88)
    args = parser.parse_args(argv)
    ret = 0
    for path in args.paths:
        with open(path, encoding='utf-8') as fd:
            content = fd.read()
        new_content = auto_walrus(content, path, line_length=args.line_length)
        if new_content is not None and content != new_content:
            sys.stdout.write(f'Rewriting {path}\n')
            with open(path, 'w', encoding='utf-8') as fd:
                fd.write(new_content)
            ret = 1
    return ret


if __name__ == '__main__':
    sys.exit(main())
