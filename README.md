# auto-walrus
Automatically use the walrus operator where possible

[![Build Status](https://github.com/MarcoGorelli/auto-walrus/workflows/tox/badge.svg)](https://github.com/MarcoGorelli/auto-walrus/actions?workflow=tox)
[![Coverage](https://codecov.io/gh/MarcoGorelli/auto-walrus/branch/main/graph/badge.svg)](https://codecov.io/gh/MarcoGorelli/auto-walrus)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MarcoGorelli/auto-walrus/main.svg)](https://results.pre-commit.ci/latest/github/MarcoGorelli/auto-walrus/main)

auto-walrus
===========

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
