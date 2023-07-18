from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import sys
from typing import Any
from typing import Iterable
from typing import Sequence
from typing import Tuple

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:
    import tomli as tomllib

SEP_SYMBOLS = frozenset(('(', ')', ',', ':'))
# name, lineno, col_offset, end_lineno, end_col_offset
Token = Tuple[str, int, int, int, int]
SIMPLE_NODE = (ast.Name, ast.Constant)
ENDS_WITH_COMMENT = re.compile(r'#.*$')
EXCLUDES = (
    r'/('
    r'\.direnv|\.eggs|\.git|\.hg|\.ipynb_checkpoints|\.mypy_cache|\.nox|\.svn|'
    r'\.tox|\.venv|'
    r'_build|buck-out|build|dist|venv'
    r')/'
)


def name_lineno_coloffset_iterable(
    tokens: Iterable[Token],
) -> list[tuple[str, int, int]]:
    return [(i[0], i[1], i[2]) for i in tokens]


def name_lineno_coloffset(tokens: Token) -> tuple[str, int, int]:
    return (tokens[0], tokens[1], tokens[2])


def is_simple_test(node: ast.AST) -> bool:
    return (
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


def record_name_lineno_coloffset(
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
                record_name_lineno_coloffset(
                    _node, end_lineno, end_col_offset,
                ),
            )
    return names


def process_if(
    node: ast.If,
    in_body_vars: dict[Token, set[Token]],
) -> set[Token]:
    _names = find_names(node.test)
    _body_names = {_name for _body in node.body for _name in find_names(_body)}
    for _name in _names:
        in_body_vars[_name] = _body_names
    return _names


def process_assign(
    node: ast.Assign,
    assignments: set[Token],
    related_vars: dict[str, list[Token]],
) -> None:
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        target = node.targets[0]
        assignments.add(
            record_name_lineno_coloffset(
                target, node.end_lineno, node.end_col_offset,
            ),
        )
        related_vars[target.id] = list(find_names(node.value))


def is_walrussable(
    _assignment: Token,
    _if_statement: Token,
    sorted_names: list[Token],
    assignment_idx: int,
    if_statement_idx: int,
    _other_assignments: list[Token],
    _other_usages: list[Token],
    names: set[Token],
    in_body_vars: dict[Token, set[Token]],
) -> bool:
    return (
        # check name doesn't appear between assignment and if statement
        _assignment[0] not in [
            sorted_names[i][0]
            for i in range(assignment_idx+1, if_statement_idx)
        ]
        # check it's the variable's only assignment
        and (len(_other_assignments) == 1)
        # check this is the first usage of this name
        and (
            name_lineno_coloffset(
                _other_usages[0],
            ) == name_lineno_coloffset(_assignment)
        )
        # check it's used at least somewhere else
        and (len(_other_usages) > 2)
        # check it doesn't appear anywhere else
        and not [
            i for i in names
            if (
                name_lineno_coloffset(i) not in
                name_lineno_coloffset_iterable(in_body_vars[_if_statement])
            )
            and (
                name_lineno_coloffset(
                    i,
                ) != name_lineno_coloffset(_assignment)
            )
            and (
                name_lineno_coloffset(
                    i,
                ) != name_lineno_coloffset(_if_statement)
            )
            and i[0] == _assignment[0]
        ]
    )


def related_vars_are_unused(
    related_vars: dict[str, list[Token]],
    name: str,
    sorted_names: list[Token],
    assignment_idx: int,
    if_statement_idx: int,
) -> bool:
    # Check that names which appear in right hand side of
    # assignment aren't used between assignment and if-statement.
    related = related_vars[name]
    should_break = False
    for rel in related:
        usages = [
            i for i in sorted_names if i[0]
            == rel[0] if i != rel
        ]
        for usage in usages:
            rel_used_idx = name_lineno_coloffset_iterable(
                sorted_names,
            ).index(name_lineno_coloffset(usage))
            if assignment_idx < rel_used_idx < if_statement_idx:
                should_break = True
    return not should_break


def visit_function_def(
    node: ast.FunctionDef,
    path: pathlib.Path,
) -> list[tuple[Token, Token]]:
    names = set()
    assignments: set[Token] = set()
    ifs = set()
    for _node in ast.walk(node):
        if isinstance(_node, ast.Name):
            names.add(record_name_lineno_coloffset(_node))

    related_vars: dict[str, list[Token]] = {}
    in_body_vars: dict[Token, set[Token]] = {}

    for _node in node.body:
        if isinstance(_node, ast.Assign):
            process_assign(_node, assignments, related_vars)
        elif isinstance(_node, ast.If):
            if is_simple_test(_node.test):
                ifs.update(process_if(_node, in_body_vars))
            for __node in _node.orelse:
                if isinstance(__node, ast.If) and is_simple_test(__node.test):
                    ifs.update(process_if(__node, in_body_vars))

    sorted_names = sorted(names, key=lambda x: (x[1], x[2]))
    sorted_assignments = sorted(assignments, key=lambda x: (x[1], x[2]))
    sorted_ifs = sorted(ifs, key=lambda x: (x[1], x[2]))
    walrus = []

    for _assignment in sorted_assignments:
        _if_statements = [i for i in sorted_ifs if i[0] == _assignment[0]]
        if len(_if_statements) != 1:
            continue
        _if_statement = _if_statements[0]
        assignment_idx = name_lineno_coloffset_iterable(
            sorted_names,
        ).index(name_lineno_coloffset(_assignment))
        if_statement_idx = name_lineno_coloffset_iterable(
            sorted_names,
        ).index(name_lineno_coloffset(_if_statement))
        _other_assignments = [
            i
            for i in sorted_assignments if i[0] == _assignment[0]
        ]
        _other_usages = [
            i for i in sorted_names if i[0] == _assignment[0]
        ]
        if is_walrussable(
            _assignment,
            _if_statement,
            sorted_names,
            assignment_idx,
            if_statement_idx,
            _other_assignments,
            _other_usages,
            names,
            in_body_vars,
        ):
            if related_vars_are_unused(
                related_vars,
                _assignment[0],
                sorted_names,
                assignment_idx,
                if_statement_idx,
            ):
                walrus.append((_assignment, _if_statement))
    return walrus


def auto_walrus(content: str, path: pathlib.Path, line_length: int) -> str | None:
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:  # pragma: no cover
        return None

    walruses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            walruses.extend(visit_function_def(node, path))
    lines_to_remove = []
    walruses = sorted(walruses, key=lambda x: (-x[1][1], -x[1][2]))

    if not walruses:
        return None

    for _assignment, _if_statement in walruses:
        if _assignment[1] != _assignment[3]:
            continue
        txt = lines[_assignment[1]-1][_assignment[2]:_assignment[4]]
        if txt.count('=') > 1:
            continue
        line = lines[_if_statement[1]-1]
        left_bit = line[:_if_statement[2]]
        right_bit = line[_if_statement[4]:]
        no_paren = any(left_bit.endswith(i) for i in SEP_SYMBOLS) and any(
            right_bit.startswith(i) for i in SEP_SYMBOLS
        )
        replace = txt.replace('=', ':=')
        if no_paren:
            line_with_walrus = left_bit + replace + right_bit
        else:
            line_with_walrus = left_bit + '(' + replace + ')' + right_bit
        if len(line_with_walrus) > line_length:
            # don't rewrite if it would split over multiple lines
            continue
        # replace assignment
        line_without_assignment = (
            f'{lines[_assignment[1]-1][:_assignment[2]]}'
            f'{lines[_assignment[1]-1][_assignment[4]:]}'
        )
        if (
            ENDS_WITH_COMMENT.search(lines[_assignment[1]-1]) is not None
        ) or (
            ENDS_WITH_COMMENT.search(lines[_if_statement[1]-1]) is not None
        ):
            continue
        lines[_assignment[1] - 1] = line_without_assignment
        # add walrus
        lines[_if_statement[1]-1] = line_with_walrus
        # remove empty line
        if not lines[_assignment[1]-1].strip():
            lines_to_remove.append(_assignment[1]-1)

    newlines = [
        line for i, line in enumerate(
            lines,
        ) if i not in lines_to_remove
    ]
    newcontent = '\n'.join(newlines)
    if newcontent and content.endswith('\n'):
        newcontent += '\n'
    if newcontent != content:
        return newcontent
    return None


def _get_config(paths: list[pathlib.Path]) -> dict[str, Any]:
    """Get the configuration from a config file.

    Search for a pyproject.toml in common parent directories
    of the given list of paths.
    """
    root = pathlib.Path(os.path.commonpath(paths))
    root = root.parent if root.is_file() else root

    while root != root.parent:

        config_file = root / 'pyproject.toml'
        if config_file.is_file():
            config = tomllib.loads(config_file.read_text())
            config = config.get('tool', {}).get('auto-walrus', {})
            if config:
                return config

        root = root.parent

    return {}


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument(
        '--files',
        help='Regex pattern with which to match files to include',
        required=False,
        default=r'',
    )
    parser.add_argument(
        '--exclude',
        help='Regex pattern with which to match files to exclude',
        required=False,
        default=r'^$',
    )
    # black formatter's default
    parser.add_argument('--line-length', type=int, default=88)
    args = parser.parse_args(argv)
    paths = [pathlib.Path(path).resolve() for path in args.paths]

    # Update defaults from pyproject.toml if present
    config = {k.replace('-', '_'): v for k, v in _get_config(paths).items()}
    parser.set_defaults(**config)
    args = parser.parse_args(argv)

    ret = 0

    for path in paths:
        if path.is_file():
            filepaths = iter((path,))
        else:
            filepaths = (
                p for p in path.rglob('*')
                if re.search(args.files, str(p), re.VERBOSE)
                and not re.search(args.exclude, str(p), re.VERBOSE)
                and not re.search(EXCLUDES, str(p))
                and p.suffix == '.py'
            )

        for filepath in filepaths:
            try:
                with open(filepath, encoding='utf-8') as fd:
                    content = fd.read()
            except UnicodeDecodeError:
                continue
            new_content = auto_walrus(content, filepath, line_length=args.line_length)
            if new_content is not None and content != new_content:
                sys.stdout.write(f'Rewriting {filepath}\n')
                with open(filepath, 'w', encoding='utf-8') as fd:
                    fd.write(new_content)
                ret = 1
    return ret


if __name__ == '__main__':
    sys.exit(main())
