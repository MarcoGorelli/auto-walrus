<h1 align="center">
auto-walrus
</h1>

<p align="center">
<img width="458" alt="auto-walrus" src="https://user-images.githubusercontent.com/33491632/194703119-156e8b6e-6461-4e2e-b946-442f3389c32b.png">
</p>

auto-walrus
===========
[![Build Status](https://github.com/MarcoGorelli/auto-walrus/workflows/tox/badge.svg)](https://github.com/MarcoGorelli/auto-walrus/actions?workflow=tox)
[![Coverage](https://codecov.io/gh/MarcoGorelli/auto-walrus/branch/main/graph/badge.svg)](https://codecov.io/gh/MarcoGorelli/auto-walrus)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MarcoGorelli/auto-walrus/main.svg)](https://results.pre-commit.ci/latest/github/MarcoGorelli/auto-walrus/main)


A tool and pre-commit hook to automatically apply the awesome walrus operator.


## Installation

```console
pip install auto-walrus
```

## Usage as a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/MarcoGorelli/auto-walrus
    rev: v0.1.5
    hooks:
    -   id: auto-walrus
```

## Command-line example

```console
auto-walrus myfile.py
```

```diff
-    n = 10
-    if n > 3:
+    if (n := 10) > 3:
```

## Configuration

Using the walrus operator can result in longer lines. Lines longer than what you
pass to ``--line-length`` won't be rewritten to use walrus operators.

E.g.
```
auto-walrus myfile_1.py myfile_2.py --line-length 89
```
