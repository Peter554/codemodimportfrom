import collections
import importlib
from typing import Optional, Union

import libcst
from libcst import RemovalSentinel, FlattenSentinel  # TODO tidy


class Transformer(libcst.CSTTransformer):
    METADATA_DEPENDENCIES = (libcst.metadata.QualifiedNameProvider,)

    def __init__(self, importfrom: str):
        self.importfrom = importfrom

        self._import_aliases_by_import = collections.defaultdict(set)
        self._import_aliases_to_remove_by_import = collections.defaultdict(set)
        self._qualified_names_to_leave = set()

    def visit_ImportFrom(self, node: "ImportFrom") -> Optional[bool]:
        if node.module.value == self.importfrom:
            for import_alias in node.names:
                self._import_aliases_by_import[node].add(import_alias)
                full_import = f"{self.importfrom}.{import_alias.name.value}"
                try:
                    # No error -> A module.
                    importlib.import_module(full_import)
                    self._qualified_names_to_leave.add(full_import)
                except ModuleNotFoundError:
                    # Error -> Not a module.
                    self._import_aliases_to_remove_by_import[node].add(import_alias)
        return False

    def leave_ImportFrom(
        self, original_node: "ImportFrom", updated_node: "ImportFrom"
    ) -> Union[
        "BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel
    ]:
        if original_node in self._import_aliases_by_import:
            if (
                self._import_aliases_by_import[original_node]
                == self._import_aliases_to_remove_by_import[original_node]
            ):
                return libcst.Import(
                    names=[libcst.ImportAlias(name=libcst.Name(value=self.importfrom))]
                )
            elif self._import_aliases_to_remove_by_import[original_node]:
                imports_to_keep = list(
                    self._import_aliases_by_import[original_node]
                    - self._import_aliases_to_remove_by_import[original_node]
                )
                return libcst.FlattenSentinel(
                    nodes=[
                        libcst.ImportFrom(
                            module=original_node.module,
                            names=imports_to_keep,
                        ),
                        libcst.Import(
                            names=[
                                libcst.ImportAlias(
                                    name=libcst.Name(value=self.importfrom)
                                )
                            ]
                        ),
                    ]
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
        qualified_name = qualified_names.pop()

        if (
            qualified_name.name not in self._qualified_names_to_leave
            and qualified_name.source == libcst.metadata.QualifiedNameSource.IMPORT
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
