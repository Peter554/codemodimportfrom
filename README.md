# codemodimportfrom

Automatically update ImportFrom statements to "import modules, not objects".

## Install

From within your project's virtual environment, install `codemodimportfrom` (as a dev dependency). e.g.

```
pip install codemodimportfrom
```

## Usage

```
# Transform all ImportFrom statements in the file path/to/file.py
codemodimportfrom path/to/file.py

# Overwrite the file
codemodimportfrom path/to/file.py --write

# Transform ImportFrom statements for modules "foo" and "bar" only
codemodimportfrom path/to/file.py --module foo --module bar

# Allow object imports for "typing.Optional" and "typing.Union"
codemodimportfrom path/to/file.py --allow typing.Optional --allow typing.Union

# Allow all object imports from typing
codemodimportfrom path/to/file.py --allow typing.*

# Parse allow list from a .txt file (one line per allowed object import)
codemodimportfrom path/to/file.py --allow allow.txt

# Also transform module imports 
# e.g. `from pydantic import dataclasses` becomes `import pydantic.dataclasses`
codemodimportfrom path/to/file.py --transform-module-imports
```

## Caveats

* Not tested with much real world code, yet.
* Relative imports (`from . import foo`) not implemented yet.
