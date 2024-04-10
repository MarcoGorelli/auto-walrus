<h1 align="center">
auto-walrus
</h1>

<p align="center">
<img width="458" alt="auto-walrus" src="https://user-images.githubusercontent.com/33491632/195613331-f7442140-09da-4376-90aa-2ac4aaa242fa.png">
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
    rev: 0.3.3
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
         print(n)
```

## Configuration

Using the walrus operator can result in longer lines. Lines longer than what you
pass to ``--line-length`` won't be rewritten to use walrus operators.

E.g.
```
auto-walrus myfile_1.py myfile_2.py --line-length 89
```

Lines with comments won't be rewritten.

## Used by

To my great surprise, this is being used by:

- https://github.com/python-graphblas/python-graphblas
- https://github.com/Remi-Gau/bids2cite
- https://github.com/TheAlgorithms/Python
- https://github.com/apache/superset

Anyone else? Please let me know, or you can open a pull request to add yourself.

## Testimonials

**Christopher Redwine**, [Senior Software Engineer at TechnologyAdvice](https://github.com/chrisRedwine)

> hmm, i dunno about this one chief

**Michael Kennedy & Brian Okken**, [hosts of the Python Bytes podcast](https://pythonbytes.fm/):

> I kind of like this being separate from other tools

**Someone on Discord**

> you're a monster

**Will McGugan**, [CEO / Founder of http://Textualize.io](https://www.willmcgugan.com/):

> Embrace the Walrus!

## Credits

Logo by [lion_space](https://www.fiverr.com/lion_space)
