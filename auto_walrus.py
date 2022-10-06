import ast
from tokenize_rt import src_to_tokens, tokens_to_src, reversed_enumerate


def first3(tokens):
    if isinstance(tokens, list):
        return [(i[0], i[1], i[2]) for i in tokens]
    return (tokens[0], tokens[1], tokens[2])

def find_names(node, end_lineno=None, end_col_offset=None):
    names = set()
    for _node in ast.walk(node):
        if isinstance(_node, ast.Name):
            names.add((_node.id, _node.lineno, _node.col_offset, end_lineno or _node.end_lineno, end_col_offset or _node.col_offset))
    return names

def visit_function_def(node):
    # record variable names
    names = set()
    assignments = set()
    ifs = set()
    for _node in ast.walk(node):
        names.update(find_names(_node))
        if isinstance(_node, ast.Assign):
            if len(_node.targets) == 1:
                target = _node.targets[0]
                assignments.update(find_names(target, _node.end_lineno, _node.end_col_offset))
        elif isinstance(_node, ast.If):
            ifs.update(find_names(_node.test))
    
    names = sorted(names, key=lambda x: (x[1], x[2]))
    assignments = sorted(assignments, key=lambda x: (x[1], x[2]))
    ifs = sorted(ifs, key=lambda x: (x[1], x[2]))

    walrus = []

    for ass in assignments:
        ifasss = [i for i in ifs if i[0] == ass[0]]
        if len(ifasss) != 1:
            continue
        ifass = ifasss[0]
        asspos = first3(names).index(first3(ass))
        ifpos = first3(names).index(first3(ifass))
        if ifpos == asspos + 1:
            if [first3(i) for i in names if i[0] == ass[0]][0] == first3(ass):
                # probably also need to check that this is the first usage
                walrus.append((ass, ifass))
    return walrus
    # check:
    # variable is assigned to
    # if it then used in an if statement
    # it is not used anywhere in between

def main(file):
    with open(file) as fd:
        content = fd.read()
    lines = content.splitlines() 
    tree = ast.parse(content)
    walruses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            walruses.extend(visit_function_def(node))

    for ass, if_ in walruses:
        if ass[1] != ass[3]:
            continue
        txt = lines[ass[1]-1][ass[2]:ass[4]]
        if txt.count('=') > 1:
            continue
        lines[ass[1]-1] = f'{lines[ass[1]-1][:ass[2]]}{lines[ass[1]-1][ass[4]:]}'
        lines[if_[1]-1] = lines[if_[1]-1].replace(ass[0], '('+txt.replace('=', ':=')+')')

    newlines = '\n'.join(lines)
    if newlines:
        newlines += '\n'
    with open(file, 'w') as fd:
        fd.write(newlines)

if __name__ == '__main__':
    import sys
    for file in sys.argv[1:]:
        main(file)