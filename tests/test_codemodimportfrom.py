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
