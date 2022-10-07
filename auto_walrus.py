import ast
from tokenize_rt import src_to_tokens, tokens_to_src, reversed_enumerate

LINE_LENGTH = 88

def first3(tokens):
    if isinstance(tokens, list):
        return [(i[0], i[1], i[2]) for i in tokens]
    return (tokens[0], tokens[1], tokens[2])

def find_names(node, end_lineno=None, end_col_offset=None):
    names = set()
    for _node in ast.walk(node):
        if isinstance(_node, ast.Name):
            names.add((_node.id, _node.lineno, _node.col_offset, end_lineno or _node.end_lineno, end_col_offset or _node.end_col_offset))
    return names

def visit_function_def(node):
    # record variable names
    names = set()
    assignments = set()
    ifs = set()
    for _node in ast.walk(node):
        names.update(find_names(_node))
    
    related_vars = {}

    for _node in node.body:
        if isinstance(_node, ast.Assign):
            if len(_node.targets) == 1 and isinstance(_node.targets[0], ast.Name):
                target = _node.targets[0]
                assignments.update(find_names(target, _node.end_lineno, _node.end_col_offset))
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

    for ass in assignments:
        ifasss = [i for i in ifs if i[0] == ass[0]]
        if len(ifasss) != 1:
            continue
        ifass = ifasss[0]
        asspos = first3(names).index(first3(ass))
        ifpos = first3(names).index(first3(ifass))
        # check name hasn't been used in between assignment
        # and if statement
        if ass[0] not in [names[i][0] for i in range(asspos+1, ifpos)]:
            # check the assignment was the variable's first usage

            # probably also need to check that none of the names in the
            # rhs appear there as well! else, the location of the
            # assignment might change the code

            this_vars_assignments = [first3(i) for i in assignments if i[0] == ass[0]]
            this_vars_names = [first3(i) for i in names if i[0] == ass[0]]
            if (
                (len(this_vars_assignments) == 1)  # check it's the variable's only assignment
                and (this_vars_names[0] == first3(ass))  # check this is the first usage of this name
                and len(this_vars_names) > 2  # check it's used at least somewhere else
            ):
                # Check that names which appear in the assignment aren't used
                # between assignment and if-statement. Otherwise, the rewrite
                # might be unsafe.
                related = related_vars[ass[0]]
                should_break = False
                for rel in related:
                    usages = [i for i in names if i[0] == rel[0] if i != rel]
                    for usage in usages:
                        rel_used_pos = first3(names).index(first3(usage))
                        if asspos < rel_used_pos < ifpos:
                            should_break = True
                if should_break:
                    continue
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
    lines_to_remove = []
    walruses = sorted(walruses, key=lambda x: (-x[1][1], -x[1][2]))
    for ass, if_ in walruses:
        if ass[1] != ass[3]:
            continue
        txt = lines[ass[1]-1][ass[2]:ass[4]]
        if txt.count('=') > 1:
            continue
        line = lines[if_[1]-1]
        # actually, if it's not used anywhere else,
        # maybe just...replace with definition?
        # I think we need a line-length parameter,
        # and we don't rewrite if we exceed the line-length
        left_bit = line[:if_[2]]
        right_bit = line[if_[4]:]
        no_paren = left_bit.endswith('(') and right_bit.startswith(')')
        replace = txt.replace('=', ':=')
        if no_paren:
            line = left_bit + replace + right_bit
        else:
            line = left_bit + '(' + replace + ')' + right_bit
        if len(line) > LINE_LENGTH:
            # don't rewrite if it would split over multiple lines
            continue
        # replace assignment
        lines[ass[1]-1] = f'{lines[ass[1]-1][:ass[2]]}{lines[ass[1]-1][ass[4]:]}'
        # add walrus
        lines[if_[1]-1] = line
        # remove empty line
        if not lines[ass[1]-1].strip():
            lines_to_remove.append(ass[1]-1)

    newlines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
    newcontent = '\n'.join(newlines)
    if newcontent:
        newcontent += '\n'
    with open(file, 'w') as fd:
        fd.write(newcontent)

if __name__ == '__main__':
    import sys
    for file in sys.argv[1:]:
        main(file)