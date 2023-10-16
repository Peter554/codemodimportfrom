import collections
import importlib
from typing import Optional, Union  # TODO tidy

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
        module_name = self._attribute_to_name(node.module)
        if module_name.startswith(self.importfrom):
            for import_alias in node.names:
                self._import_aliases_by_import[node].add(import_alias)
                full_import = f"{module_name}.{import_alias.name.value}"
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
        module_name = self._attribute_to_name(original_node.module)
        if original_node in self._import_aliases_by_import:
            imports_to_remove = self._import_aliases_to_remove_by_import[original_node]
            imports_to_keep = (
                self._import_aliases_by_import[original_node] - imports_to_remove
            )
            if not imports_to_keep:
                return libcst.Import(
                    names=[
                        libcst.ImportAlias(name=self._name_to_attribute(module_name))
                    ]
                )
            elif imports_to_remove:
                return libcst.FlattenSentinel(
                    nodes=[
                        libcst.ImportFrom(
                            module=original_node.module,
                            names=list(imports_to_keep),
                        ),
                        libcst.Import(
                            names=[
                                libcst.ImportAlias(
                                    name=self._name_to_attribute(module_name)
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
            and qualified_name.name.startswith(f"{self.importfrom}.")
        ):
            return self._name_to_attribute(qualified_name.name)
        return updated_node

    def _attribute_to_name(self, attribute: libcst.Attribute | libcst.Name) -> str:
        if isinstance(attribute, libcst.Name):
            return attribute.value
        else:
            return self._attribute_to_name(attribute.value) + "." + attribute.attr.value

    def _name_to_attribute(self, name: str) -> libcst.Attribute | libcst.Name:
        if "." not in name:
            return libcst.Name(value=name)
        l, r = name.rsplit(".", 1)
        return libcst.Attribute(
            value=self._name_to_attribute(l), attr=libcst.Name(value=r)
        )


def transform_importfrom(*, code: str, importfrom: str) -> str:
    tree = libcst.parse_module(code)
    wrapper = libcst.metadata.MetadataWrapper(tree)
    tree = wrapper.visit(Transformer(importfrom))
    return tree.code  # TODO black, optimize imports (isort/ruff)?
