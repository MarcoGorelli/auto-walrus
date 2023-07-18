from __future__ import annotations

import pathlib
from typing import Any
from typing import List
from typing import Tuple

import pytest

from auto_walrus import auto_walrus
from auto_walrus import main


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
            '    if a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if a > 3:\n'
            '        print(a)\n',
            'def foo():\n'
            '    if (a := 0) > 3:\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if a:\n'
            '        print(a)\n'
            '    else:\n'
            '        pass\n',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)\n'
            '    else:\n'
            '        pass\n',
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
            '    if a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    print(0)\n'
            '    if (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if (a):\n'
            '        print(a)\n',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)\n',
        ),
        (
            'def foo():\n'
            '    b = 0; a = 0\n'
            '    if a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    b = 0; \n'
            '    if (a := 0):\n'
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
        (
            'def foo():\n'
            '    a = 0\n'
            '    if a:\n'
            '        print(a)\n'
            '    if (b := 3) > 0:\n'
            '        print(b)\n',
            'def foo():\n'
            '    if (a := 0):\n'
            '        print(a)\n'
            '    if (b := 3) > 0:\n'
            '        print(b)\n',
        ),
        (
            'def foo():\n'
            '    a = 0\n'
            '    if np.sin(b) + np.cos(b) < np.tan(b):\n'
            '        pass\n'
            '    elif a:\n'
            '        print(a)\n',
            'def foo():\n'
            '    if np.sin(b) + np.cos(b) < np.tan(b):\n'
            '        pass\n'
            '    elif (a := 0):\n'
            '        print(a)\n',
        ),
    ],
)
def test_rewrite(src: str, expected: str) -> None:
    ret = auto_walrus(src, pathlib.Path('t.py'), 88)
    assert ret == expected


@pytest.mark.parametrize(
    'src',
    [
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
        'def foo():\n'
        '    a = 0  # no-walrus\n'
        '    if a:\n'
        '        print(a)\n',
        'def foo():\n'
        '    a = 0\n'
        '    if a:  # no-walrus\n'
        '        print(a)\n',
        'n = 10\n'
        'if foo(a := n+1):\n'
        '    print(n)\n',
        'a = 0\n'
        'if False and a:\n'
        '    print(a)\n'
        'else:\n'
        '    print(a)\n',
        'def foo():\n'
        '    a = 1\n'
        '    if a:\n'
        '        print(a)\n'
        '    a = 2\n',
        'def foo():\n'
        '    n = 10\n'
        '    if True:\n'
        '        pass\n'
        '    elif foo(a := n+1):\n'
        '        print(n)\n',
        'def foo():\n'
        '    n = 10\n'
        '    if n > np.sin(foo.bar.quox):\n'
        '        print(n)\n',
        'def foo():\n'
        '    n = 10\n'
        '    if True or n > 3:\n'
        '        print(n)\n',
    ],
)
def test_noop(src: str) -> None:
    ret = auto_walrus(src, pathlib.Path('t.py'), 40)
    assert ret is None


ProjectDirT = Tuple[pathlib.Path, List[pathlib.Path]]

SRC_ORIG = (
    'def foo():\n'
    '    a = 0\n'
    '    if a:\n'
    '        print(a)\n'
)
SRC_CHANGED = (
    'def foo():\n'
    '    if (a := 0):\n'
    '        print(a)\n'
)


@pytest.fixture
def project_dir(request: Any, tmp_path: pathlib.Path) -> ProjectDirT:
    # tmp_path will be the root of the project, e.g.:
    # tmp_path
    # ├── submodule1/
    # |   ├── submodule2/
    # |   |   └── a.py
    # |   └── b.py
    # ├── submodule3/
    # |   └── c.py
    # └── pyproject.toml

    config_content = request.node.get_closest_marker('config_content')
    if config_content:
        (tmp_path / 'pyproject.toml').write_text(config_content.args[0])

    python_files = [
        tmp_path / 'submodule1' / 'submodule2' / 'a.py',
        tmp_path / 'submodule1' / 'b.py',
        tmp_path / 'submodule3' / 'c.py',
    ]
    for file_path in python_files:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(SRC_ORIG)

    return tmp_path, python_files


PROJECT_CONFIG_EXCLUDE_A = (
    '[tool.auto-walrus]\n'
    'exclude = "/a"\n'
)


@pytest.mark.config_content(PROJECT_CONFIG_EXCLUDE_A)
def test_config_file_respected(project_dir: ProjectDirT) -> None:
    project_root, files = project_dir
    main([str(project_root)])
    for file in files:
        expected = SRC_ORIG if file.name == 'a.py' else SRC_CHANGED
        assert file.read_text() == expected, f'Unexpected result for {file}'


@pytest.mark.config_content(PROJECT_CONFIG_EXCLUDE_A)
def test_config_file_overridden_by_cmdline(
    project_dir: ProjectDirT,
) -> None:
    project_root, files = project_dir
    main(['--exclude', '/b', str(project_root)])
    for file in files:
        expected = SRC_ORIG if file.name == 'b.py' else SRC_CHANGED
        assert file.read_text() == expected, f'Unexpected result for {file}'


@pytest.mark.config_content('\n')
def test_config_file_no_auto_walrus(project_dir: ProjectDirT) -> None:
    project_root, files = project_dir
    main([str(project_root)])
    for file in files:
        assert file.read_text() == SRC_CHANGED, f'Unexpected result for {file}'


def test_config_file_missing(project_dir: ProjectDirT) -> None:
    project_root, files = project_dir
    main([str(project_root)])
    for file in files:
        assert file.read_text() == SRC_CHANGED, f'Unexpected result for {file}'
