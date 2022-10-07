import pytest

from auto_walrus import auto_walrus


@pytest.mark.parametrize(
    'src, expected',
    [
        (
            'def foo():\n'
            '    a = 0\n'
            '    if a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if True:\n'
            '        print(1)\n'
            '    elif a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    if True:\n'
            '        print(1)\n'
            '    elif (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    print(0)\n'
            '    while a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    print(0)\n'
            '    while (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    while (a):\n'
            '        print(a)\n',
            'def foo():\n'
            '    while (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    b = 0; a = 0\n'
            '    while a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    b = 0; \n'
            '    while (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if a:\n'
            '        print(a)',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)',
        ),
    ],
)
def test_rewrite(src: str, expected: str) -> None:
    ret = auto_walrus(src, 't.py', 88)
    assert ret == expected


@pytest.mark.parametrize(
    'src',
    [
        # middle variable
        'def foo():\n'
        '    b = [0]\n'
        '    a = b[0]\n'
        '    b[0] = 1\n'
        '    if a:\n'
        '        print(a)\n',
        'def foo():\n'
        '    a = 1\n'
        '    a = 2\n'
        '    if a:\n'
        '        print(a)\n',
        'def foo():\n'
        '    a = (\n'
        '        0,)\n'
        '    if a:\n'
        '        print(a)\n',
        'def foo():\n'
        '    a = (b==True)\n'
        '    if a:\n'
        '        print(a)\n',
        'def foo():\n'
        '    a = thequickbrownfoxjumpsoverthelazydog\n'
        '    if a:\n'
        '        print(a)\n',
    ],
)
def test_noop(src: str) -> None:
    ret = auto_walrus(src, 't.py', 20)
    assert ret is None
