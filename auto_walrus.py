from __future__ import annotations

import argparse
import ast
import sys
from typing import Sequence

SEP_SYMBOLS = frozenset(('(', ')', ',', ':'))


def name_lineno_coloffset(tokens):
    if isinstance(tokens, list):
        return [(i[0], i[1], i[2]) for i in tokens]
    return (tokens[0], tokens[1], tokens[2])


def record_name_lineno_coloffset(node, end_lineno=None, end_col_offset=None):
    return (
        node.id, node.lineno, node.col_offset,
        end_lineno or node.end_lineno,
        end_col_offset or node.end_col_offset,
    )


def find_names(node, end_lineno=None, end_col_offset=None):
    names = set()
    for _node in ast.walk(node):
        if isinstance(_node, ast.Name):
            names.add(
                record_name_lineno_coloffset(
                    _node, end_lineno, end_col_offset,
                ),
            )
    return names


def visit_function_def(node, path):
    names = set()
    assignments = set()
    ifs = set()
    for _node in ast.walk(node):
        names.update(find_names(_node))

    related_vars = {}

    for _node in node.body:
        if isinstance(_node, ast.Assign):
            if (
                len(_node.targets) == 1
                and isinstance(_node.targets[0], ast.Name)
            ):
                target = _node.targets[0]
                assignments.add(
                    record_name_lineno_coloffset(
                        target, _node.end_lineno, _node.end_col_offset,
                    ),
                )
                related_vars[target.id] = list(find_names(_node.value))
        elif isinstance(_node, ast.If):
            ifs.update(find_names(_node.test))
            for __node in _node.orelse:
                if isinstance(__node, ast.If):
                    ifs.update(find_names(__node.test))
        elif isinstance(_node, (ast.If, ast.While)):
            ifs.update(find_names(_node.test))

    names = sorted(names, key=lambda x: (x[1], x[2]))
    assignments = sorted(assignments, key=lambda x: (x[1], x[2]))
    ifs = sorted(ifs, key=lambda x: (x[1], x[2]))
    walrus = []

    for _assignment in assignments:
        _if_statements = [i for i in ifs if i[0] == _assignment[0]]
        if len(_if_statements) != 1:
            continue
        _if_statement = _if_statements[0]
        assignment_idx = name_lineno_coloffset(
            names,
        ).index(name_lineno_coloffset(_assignment))
        if_statement_idx = name_lineno_coloffset(
            names,
        ).index(name_lineno_coloffset(_if_statement))
        _other_assignments = [
            name_lineno_coloffset(i)
            for i in assignments if i[0] == _assignment[0]
        ]
        _other_usages = [
            name_lineno_coloffset(
                i,
            ) for i in names if i[0] == _assignment[0]
        ]
        if (
            # check name doesn't appear between assignment and if statement
            _assignment[0] not in [
                names[i][0]
                for i in range(assignment_idx+1, if_statement_idx)
            ]
            # check it's the variable's only assignment
            and (len(_other_assignments) == 1)
            # check this is the first usage of this name
            and (_other_usages[0] == name_lineno_coloffset(_assignment))
            # check it's used at least somewhere else
            and len(_other_usages) > 2
        ):
            # Check that names which appear in right hand side of
            # assignment aren't used between assignment and if-statement.
            related = related_vars[_assignment[0]]
            should_break = False
            for rel in related:
                usages = [i for i in names if i[0] == rel[0] if i != rel]
                for usage in usages:
                    rel_used_idx = name_lineno_coloffset(
                        names,
                    ).index(name_lineno_coloffset(usage))
                    if assignment_idx < rel_used_idx < if_statement_idx:
                        should_break = True
            if should_break:
                continue
            walrus.append((_assignment, _if_statement))
    return walrus


def auto_walrus(content, path, line_length):
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:  # pragma: no cover
        return 0

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
