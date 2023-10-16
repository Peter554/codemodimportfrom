import collections
import importlib
import functools

import libcst as cst


def transform_importfrom(
    *,
    code: str,
    modules: list[str] | None = None,
    allow_list: list[str] | None = None,
    transform_module_imports: bool = False,
) -> str:
    tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(tree)
    tree = wrapper.visit(
        Transformer(modules or [], allow_list or [], transform_module_imports)
    )
    return tree.code


class Transformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (cst.metadata.QualifiedNameProvider,)

    def __init__(
        self, modules: list[str], allow_list: list[str], transform_module_imports: bool
    ):
        self.modules = modules
        self.transform_module_imports = transform_module_imports

        self._imports_from = set()
        self._import_aliases_by_import = collections.defaultdict(set)
        self._imports_to_add_by_import = collections.defaultdict(set)
        self._import_aliases_to_remove_by_import = collections.defaultdict(set)
        self._qualified_names_to_leave = set(allow_list)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        if node.module is None:
            return
        module_name = self._attribute_to_name(node.module)
        if not self.modules or any(
            module_name == module or module_name.startswith(module + ".")
            for module in self.modules
        ):
            self._imports_from.add(module_name)
            for import_alias in node.names:
                self._import_aliases_by_import[node].add(import_alias)
                full_import = f"{module_name}.{import_alias.name.value}"
                if self._matches_qualified_name_to_leave(full_import):
                    continue
                is_module = self._is_module(full_import)
                if is_module:
                    if self.transform_module_imports:
                        self._imports_to_add_by_import[node].add(
                            f"{module_name}.{import_alias.name.value}"
                        )
                        self._import_aliases_to_remove_by_import[node].add(import_alias)
                    else:
                        self._qualified_names_to_leave.add(full_import)
                else:
                    self._imports_to_add_by_import[node].add(module_name)
                    self._import_aliases_to_remove_by_import[node].add(import_alias)

        return False

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.BaseSmallStatement | cst.FlattenSentinel[
        cst.BaseSmallStatement
    ] | cst.RemovalSentinel:
        if original_node in self._import_aliases_by_import:
            nodes = []
            imports_to_add = self._imports_to_add_by_import[original_node]
            imports_to_remove = self._import_aliases_to_remove_by_import[original_node]
            imports_to_keep = (
                self._import_aliases_by_import[original_node] - imports_to_remove
            )
            if imports_to_keep:
                nodes.append(
                    cst.ImportFrom(
                        module=original_node.module,
                        names=[
                            imports_to_keep.with_changes(
                                comma=cst.MaybeSentinel.DEFAULT
                            )
                            for imports_to_keep in list(imports_to_keep)
                        ],
                    )
                )
            if imports_to_add:
                for import_to_add in sorted(imports_to_add):
                    nodes.append(
                        cst.Import(
                            names=[
                                cst.ImportAlias(
                                    name=self._name_to_attribute(import_to_add)
                                )
                            ]
                        )
                    )
            return cst.FlattenSentinel(nodes=nodes)
        return updated_node

    def leave_Name(
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.BaseExpression:
        qualified_names = self.get_metadata(
            cst.metadata.QualifiedNameProvider, original_node
        )
        if len(qualified_names) == 0:
            return updated_node
        if len(qualified_names) > 1:
            raise Exception  # TODO
        qualified_name = qualified_names.pop()

        if (
            not self._matches_qualified_name_to_leave(qualified_name.name)
            and qualified_name.source == cst.metadata.QualifiedNameSource.IMPORT
            and any(
                qualified_name.name.startswith(f"{imports_from}.")
                for imports_from in self._imports_from
            )
        ):
            return self._name_to_attribute(qualified_name.name)
        return updated_node

    def _attribute_to_name(self, attribute: cst.Attribute | cst.Name) -> str:
        if isinstance(attribute, cst.Name):
            return attribute.value
        else:
            assert isinstance(attribute.value, (cst.Attribute, cst.Name))
            return self._attribute_to_name(attribute.value) + "." + attribute.attr.value

    def _name_to_attribute(self, name: str) -> cst.Attribute | cst.Name:
        if "." not in name:
            return cst.Name(value=name)
        l, r = name.rsplit(".", 1)
        return cst.Attribute(value=self._name_to_attribute(l), attr=cst.Name(value=r))

    def _matches_qualified_name_to_leave(self, qualified_name: str) -> bool:
        for qualified_name_to_leave in self._qualified_names_to_leave:
            if qualified_name_to_leave.endswith(".*") and qualified_name.startswith(
                qualified_name_to_leave.removesuffix(".*") + "."
            ):
                return True
            elif qualified_name == qualified_name_to_leave:
                return True
        return False

    @functools.cache
    def _is_module(self, path: str) -> bool:
        try:
            importlib.import_module(path)
        except ModuleNotFoundError:
            return False
        else:
            return True
