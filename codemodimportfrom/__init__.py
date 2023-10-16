from typing import Optional, Union

import libcst
from libcst import RemovalSentinel, FlattenSentinel  # TODO tidy


class Transformer(libcst.CSTTransformer):
    METADATA_DEPENDENCIES = (libcst.metadata.QualifiedNameProvider,)

    def __init__(self, importfrom: str):
        self.importfrom = importfrom

        self._imports_to_replace = set()

    def visit_ImportFrom(self, node: "ImportFrom") -> Optional[bool]:
        if node.module.value == self.importfrom:
            self._imports_to_replace.add(node)
        return False

    def leave_ImportFrom(
        self, original_node: "ImportFrom", updated_node: "ImportFrom"
    ) -> Union[
        "BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel
    ]:
        if original_node in self._imports_to_replace:
            return libcst.Import(
                names=[libcst.ImportAlias(name=libcst.Name(value=self.importfrom))]
            )
        return updated_node

    def leave_Name(
        self, original_node: "Name", updated_node: "Name"
    ) -> "BaseExpression":
        qualified_names = self.get_metadata(
            libcst.metadata.QualifiedNameProvider, original_node
        )
        if len(qualified_names) == 0:
            return updated_node
        if len(qualified_names) > 1:
            raise Exception  # TODO
        qualified_name: libcst.metadata.QualifiedName = qualified_names.pop()

        if (
            qualified_name.source == libcst.metadata.QualifiedNameSource.IMPORT
            and qualified_name.name == f"{self.importfrom}.{original_node.value}"
        ):
            return libcst.Attribute(
                value=libcst.Name(value=self.importfrom),
                attr=libcst.Name(value=original_node.value),
            )
        return updated_node


def transform_importfrom(*, code: str, importfrom: str) -> str:
    tree = libcst.parse_module(code)
    wrapper = libcst.metadata.MetadataWrapper(tree)
    tree = wrapper.visit(Transformer(importfrom))
    return tree.code  # TODO black, optimize imports (isort/ruff)?
