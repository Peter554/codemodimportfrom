from typing import Optional, Union

import libcst
from libcst import RemovalSentinel, FlattenSentinel  # TODO tidy


class Transformer(libcst.CSTTransformer):
    def __init__(self, importfrom: str):
        self.importfrom = importfrom

        self._imports_to_replace = set()
        self._names_to_replace = set()
        self._attributes = []

    def visit_ImportFrom(self, node: "ImportFrom") -> Optional[bool]:
        if node.module.value == self.importfrom:
            self._imports_to_replace.add(node)
            for name in node.names:
                self._names_to_replace.add(name.name.value)
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
        else:
            return updated_node

    def visit_Attribute(self, node: "Attribute") -> Optional[bool]:
        self._attributes.append(node)

    def leave_Attribute(
        self, original_node: "Attribute", updated_node: "Attribute"
    ) -> "BaseExpression":
        self._attributes.pop()
        return updated_node

    def leave_Name(
        self, original_node: "Name", updated_node: "Name"
    ) -> "BaseExpression":
        if original_node.value in self._names_to_replace:
            name_to_replace = original_node.value
            first_attribute = self._attributes[0].value if self._attributes else None
            if (
                not self._attributes
                or (
                    isinstance(first_attribute, libcst.Name)
                    and first_attribute.value == name_to_replace
                )
                or (
                    isinstance(first_attribute, libcst.Call)
                    and isinstance(first_attribute.func, libcst.Name)
                    and first_attribute.func.value == name_to_replace
                )
            ):
                return libcst.Attribute(
                    value=libcst.Name(value=self.importfrom),
                    attr=libcst.Name(value=name_to_replace),
                )
        return updated_node


def transform_importfrom(*, code: str, importfrom: str) -> str:
    tree = libcst.parse_module(code)
    # print(tree)  # TODO
    transformer = Transformer(importfrom)
    tree = tree.visit(transformer)
    return tree.code  # TODO black, optimize imports (isort/ruff)?
