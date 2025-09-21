# mypy: ignore
# ruff: noqa: INP001
import re
import subprocess
import sys

how = sys.argv[1]

with open("pyproject.toml", encoding="utf-8") as f:
    content = f.read()
old_version = re.search(r'version = "(.*)"', content).group(1)
version = old_version.split(".")
if how == "patch":
    version = ".".join(version[:-1] + [str(int(version[-1]) + 1)])
elif how == "minor":
    version = ".".join(version[:-2] + [str(int(version[-2]) + 1), "0"])
elif how == "major":
    version = ".".join([str(int(version[0]) + 1), "0", "0"])
content = content.replace(f'version = "{old_version}"', f'version = "{version}"')
with open("pyproject.toml", "w", encoding="utf-8") as f:
    f.write(content)

with open("README.md", encoding="utf-8") as f:
    content = f.read()
content = content.replace(
    f"rev: {old_version}",
    f"rev: {version}",
)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

subprocess.run(["git", "commit", "-a", "-m", f"Bump version to {version}"], check=True)
subprocess.run(["git", "tag", "-a", version, "-m", version], check=True)
subprocess.run(["git", "push", "--follow-tags"], check=True)
