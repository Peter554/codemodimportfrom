import codemodimportfrom


def test_rewrites_imports():
    code = """
from foo import a, b
from bar import c, d
import bax

a
b()

a.x
b().y

c
d()

bax.a
bax.a(a)
bax.a[0](a)
""".strip()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code, importfrom="foo"
    )

    assert (
        transformed_code
        == """
import foo
from bar import c, d
import bax

foo.a
foo.b()

foo.a.x
foo.b().y

c
d()

bax.a
bax.a(foo.a)
bax.a[0](foo.a)
""".strip()
    )
