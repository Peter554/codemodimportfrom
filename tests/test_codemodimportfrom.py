import pytest

from codemodimportfrom import codemodimportfrom


@pytest.mark.parametrize(
    "code,expected_transformed_code",
    [
        ["", ""],
        #
        ["# foo", "# foo"],
        #
        [
            """
from foo import a, b
a
b()""",
            """
import foo
foo.a
foo.b()""",
        ],
        #
        [
            """
from foo import a
from bar import b
a
b""",
            """
import foo
from bar import b
foo.a
b""",
        ],
        #
        [
            """
from foo import a
from bar import b
a.a
b.a""",
            """
import foo
from bar import b
foo.a.a
b.a""",
        ],
        #
        [
            """
from foo import a
a
def bar():
    x = a.x
    a = A()
    b = a.b
a""",
            """
import foo
foo.a
def bar():
    x = foo.a.x
    a = A()
    b = a.b
foo.a""",
        ],
        #
        [
            """
from foo import a
a
class Foo:
    a: int""",
            """
import foo
foo.a
class Foo:
    a: int""",
        ],
    ],
)
def test_rewrites_imports(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, modules=["foo"]
    )

    assert transformed_code == expected_transformed_code


@pytest.mark.parametrize(
    "code,expected_transformed_code",
    [
        [
            """
from foo import a as aa, b
aa
b()""",
            """
import foo
foo.a
foo.b()""",
        ],
        #
        [
            """
from foo import a as aa, b as bb
aa
bb()""",
            """
import foo
foo.a
foo.b()""",
        ],
        #
        [
            """
from foo import a as aa
from bar import aa as a
aa
a""",
            """
import foo
from bar import aa as a
foo.a
a""",
        ],
        #
        [
            """
from foo import a as aa
from foo.bar import aa as a
aa
a""",
            """
import foo
import foo.bar
foo.a
foo.bar.aa""",
        ],
    ],
)
def test_handles_import_aliases(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, modules=["foo"]
    )

    assert transformed_code == expected_transformed_code


@pytest.mark.parametrize(
    "code, expected_transformed_code",
    [
        [
            """
from foo.bar import a, b
from foo import c, d
a
b()
c
d()""",
            """
import foo.bar
import foo
foo.bar.a
foo.bar.b()
foo.c
foo.d()""",
        ],
    ],
)
def test_handles_dotted_imports(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, modules=["foo"]
    )

    assert transformed_code == expected_transformed_code


@pytest.mark.parametrize(
    "code, expected_transformed_code",
    [
        [
            """
from pydantic import BaseModel
BaseModel""",
            """
import pydantic
pydantic.BaseModel""",
        ],
        #
        [
            """
from pydantic import dataclasses
dataclasses""",
            """
from pydantic import dataclasses
dataclasses""",
        ],
        #
        [
            """
from pydantic import BaseModel, dataclasses
BaseModel
dataclasses""",
            """
from pydantic import dataclasses; import pydantic
pydantic.BaseModel
dataclasses""",
        ],
        #
        [
            """
from pydantic import BaseModel as PydanticBaseModel, dataclasses as pydantic_dataclasses
PydanticBaseModel
pydantic_dataclasses""",
            """
from pydantic import dataclasses as pydantic_dataclasses; import pydantic
pydantic.BaseModel
pydantic_dataclasses""",
        ],
        #
        [
            """
from pydantic.v1 import BaseModel, dataclasses as pydantic_dataclasses
from pydantic import ValidationError
BaseModel
pydantic_dataclasses
ValidationError""",
            """
from pydantic.v1 import dataclasses as pydantic_dataclasses; import pydantic.v1
import pydantic
pydantic.v1.BaseModel
pydantic_dataclasses
pydantic.ValidationError""",
        ],
    ],
)
def test_does_not_rewrite_module_imports(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, modules=["pydantic"]
    )

    assert transformed_code == expected_transformed_code


@pytest.mark.parametrize(
    "code, expected_transformed_code",
    [
        [
            """
from pydantic import BaseModel
BaseModel""",
            """
from pydantic import BaseModel
BaseModel""",
        ],
        #
        [
            """
from pydantic import BaseModel, ValidationError
BaseModel
ValidationError""",
            """
from pydantic import BaseModel; import pydantic
BaseModel
pydantic.ValidationError""",
        ],
        #
        [
            """
from pydantic import BaseModel as BM, ValidationError
BM
ValidationError""",
            """
from pydantic import BaseModel as BM; import pydantic
BM
pydantic.ValidationError""",
        ],
        #
        [
            """
from pydantic import BaseModel, ValidationError
from pydantic.v1 import BaseModel as V1BaseModel, ValidationError as V1ValidationError
BaseModel
ValidationError
V1BaseModel
V1ValidationError""",
            """
from pydantic import BaseModel; import pydantic
from pydantic.v1 import BaseModel as V1BaseModel; import pydantic.v1
BaseModel
pydantic.ValidationError
V1BaseModel
pydantic.v1.ValidationError""",
        ],
    ],
)
def test_respects_allowlist(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code,
        modules=["pydantic"],
        allow_list=["pydantic.BaseModel", "pydantic.v1.BaseModel"],
    )

    assert transformed_code == expected_transformed_code


@pytest.mark.parametrize(
    "code, expected_transformed_code",
    [
        [
            """
from pydantic.v1 import BaseModel
BaseModel""",
            """
from pydantic.v1 import BaseModel
BaseModel""",
        ],
        #
        [
            """
from pydantic.v1 import BaseModel as V1BaseModel, ValidationError as V1ValidationError
from pydantic import BaseModel, ValidationError
V1BaseModel
V1ValidationError
BaseModel
ValidationError""",
            """
from pydantic.v1 import BaseModel as V1BaseModel, ValidationError as V1ValidationError
import pydantic
V1BaseModel
V1ValidationError
pydantic.BaseModel
pydantic.ValidationError""",
        ],
    ],
)
def test_respects_allowlist_with_wildcards(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code,
        modules=["pydantic"],
        allow_list=["pydantic.v1.*"],
    )

    assert transformed_code == expected_transformed_code


def test_handles_multiple_modules():
    code = """
from foo import a
from bar import b
from baz import c
a
b
c""".strip()

    assert (
        codemodimportfrom.transform_importfrom(code=code, modules=["foo", "baz"])
        == """
import foo
from bar import b
import baz
foo.a
b
baz.c""".strip()
    )

    assert (
        codemodimportfrom.transform_importfrom(code=code)
        == """
import foo
import bar
import baz
foo.a
bar.b
baz.c""".strip()
    )


@pytest.mark.parametrize(
    "code, expected_transformed_code",
    [
        [
            """
from pydantic import dataclasses
dataclasses""",
            """
import pydantic.dataclasses
pydantic.dataclasses""",
        ],
        #
        [
            """
from pydantic import dataclasses, BaseModel
dataclasses
BaseModel""",
            """
import pydantic; import pydantic.dataclasses
pydantic.dataclasses
pydantic.BaseModel""",
        ],
        #
        [
            """
from pydantic import dataclasses, BaseModel, ValidationError
dataclasses
BaseModel
ValidationError""",
            """
from pydantic import ValidationError; import pydantic; import pydantic.dataclasses
pydantic.dataclasses
pydantic.BaseModel
ValidationError""",
        ],
        #
        [
            """
from pydantic import dataclasses, BaseModel, ValidationError
from pydantic.v1 import dataclasses as v1_dataclasses, BaseModel as V1BaseModel, ValidationError as V1ValidationError
dataclasses
BaseModel
ValidationError
v1_dataclasses
V1BaseModel
V1ValidationError""",
            """
from pydantic import ValidationError; import pydantic; import pydantic.dataclasses
from pydantic.v1 import BaseModel as V1BaseModel; import pydantic.v1; import pydantic.v1.dataclasses
pydantic.dataclasses
pydantic.BaseModel
ValidationError
pydantic.v1.dataclasses
V1BaseModel
pydantic.v1.ValidationError""",
        ],
    ],
)
def test_handles_transform_module_imports(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code,
        modules=["pydantic"],
        allow_list=["pydantic.ValidationError", "pydantic.v1.BaseModel"],
        transform_module_imports=True,
    )

    assert transformed_code == expected_transformed_code
