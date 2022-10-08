<h1 align="center">
auto-walrus
</h1>

<p align="center">
<img width="458" alt="auto-walrus" src="https://user-images.githubusercontent.com/33491632/194700764-9b9ace34-62c2-403e-9141-edd0e38e8943.png">
</p>

auto-walrus
===========
[![Build Status](https://github.com/MarcoGorelli/auto-walrus/workflows/tox/badge.svg)](https://github.com/MarcoGorelli/auto-walrus/actions?workflow=tox)
[![Coverage](https://codecov.io/gh/MarcoGorelli/auto-walrus/branch/main/graph/badge.svg)](https://codecov.io/gh/MarcoGorelli/auto-walrus)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MarcoGorelli/auto-walrus/main.svg)](https://results.pre-commit.ci/latest/github/MarcoGorelli/auto-walrus/main)


A tool and pre-commit hook to automatically apply the awesome walrus operator.


## Installation

```console
$ pip install auto-walrus
```

## Usage as a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/MarcoGorelli/auto-walrus
    rev: v0.1.3
    hooks:
    -   id: auto-walrus
```

## Command-line example

```console
$ auto-walrus myfile.py
```

```diff
-    n = len(a)
-    if n > 10:
+    if (n := len(a)) > 10:
```

## Configuration

Using the walrus operator can result in longer lines. Lines longer than what you
pass to ``--line-length`` won't be rewritten to use walrus operators.

E.g.
```
$ auto-walrus myfile_1.py myfile_2.py --line-length 89
```
