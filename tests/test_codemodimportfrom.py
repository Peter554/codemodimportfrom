import pytest

import codemodimportfrom


@pytest.mark.parametrize(
    "code,expected_transformed_code",
    [
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
        code=code, importfrom="foo"
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
    ],
)
def test_handles_import_aliases(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, importfrom="foo"
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
    ],
)
def test_does_not_rewrite_module_imports(code, expected_transformed_code):
    code = code.strip()
    expected_transformed_code = expected_transformed_code.strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, importfrom="pydantic"
    )

    assert transformed_code == expected_transformed_code
