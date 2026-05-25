from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests.repository_test_support import ROOT


PACKAGE_ROOT = ROOT / "src" / "quizbank_mvp"
PACKAGE_NAME = "quizbank_mvp"


def package_modules() -> dict[str, Path]:
    modules = {}
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).with_suffix("")
        if relative.name == "__init__":
            module_name = PACKAGE_NAME
        else:
            module_name = f"{PACKAGE_NAME}.{relative.as_posix().replace('/', '.')}"
        modules[module_name] = path
    return modules


def runtime_import_graph(modules: dict[str, Path]) -> dict[str, set[str]]:
    module_names = set(modules)
    return {
        module_name: runtime_imports(module_name, path, module_names)
        for module_name, path in modules.items()
    }


def runtime_imports(module_name: str, path: Path, module_names: set[str]) -> set[str]:
    visitor = RuntimeImportVisitor(module_name, module_names)
    visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
    visitor.imports.discard(module_name)
    return visitor.imports


class RuntimeImportVisitor(ast.NodeVisitor):
    def __init__(self, module_name: str, module_names: set[str]) -> None:
        self.module_name = module_name
        self.module_names = module_names
        self.imports: set[str] = set()

    def visit_If(self, node: ast.If) -> None:
        if is_type_checking_guard(node.test):
            for child in node.orelse:
                self.visit(child)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.add_module(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "__future__":
            return
        target = self.resolve_import_from_target(node)
        if target is None:
            return
        alias_targets = [f"{target}.{alias.name}" for alias in node.names]
        if any(self.add_module(alias_target) for alias_target in alias_targets):
            return
        self.add_module(target)

    def resolve_import_from_target(self, node: ast.ImportFrom) -> str | None:
        if node.level == 0:
            return node.module
        package = self.current_package()
        package_parts = package.split(".")
        if node.level > 1:
            package_parts = package_parts[: -(node.level - 1)]
        if not package_parts:
            return None
        target = ".".join(package_parts)
        if node.module:
            target = f"{target}.{node.module}"
        return target

    def current_package(self) -> str:
        if self.module_name == PACKAGE_NAME:
            return self.module_name
        return self.module_name.rsplit(".", 1)[0]

    def add_module(self, imported_name: str | None) -> bool:
        if not imported_name or not imported_name.startswith(PACKAGE_NAME):
            return False
        for candidate in module_prefixes(imported_name):
            if candidate in self.module_names:
                self.imports.add(candidate)
                return True
        return False


def module_prefixes(imported_name: str) -> list[str]:
    parts = imported_name.split(".")
    return [".".join(parts[:index]) for index in range(len(parts), 0, -1)]


def is_type_checking_guard(test: ast.AST) -> bool:
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    state = TarjanState()
    for module_name in sorted(graph):
        if module_name not in state.indexes:
            visit_component(module_name, graph, state)
    return state.components


class TarjanState:
    def __init__(self) -> None:
        self.indexes: dict[str, int] = {}
        self.lowlinks: dict[str, int] = {}
        self.stack: list[str] = []
        self.on_stack: set[str] = set()
        self.components: list[list[str]] = []


def visit_component(module_name: str, graph: dict[str, set[str]], state: TarjanState) -> None:
    state.indexes[module_name] = len(state.indexes)
    state.lowlinks[module_name] = state.indexes[module_name]
    state.stack.append(module_name)
    state.on_stack.add(module_name)
    for dependency in sorted(graph[module_name]):
        if dependency not in state.indexes:
            visit_component(dependency, graph, state)
            state.lowlinks[module_name] = min(state.lowlinks[module_name], state.lowlinks[dependency])
        elif dependency in state.on_stack:
            state.lowlinks[module_name] = min(state.lowlinks[module_name], state.indexes[dependency])
    if state.lowlinks[module_name] == state.indexes[module_name]:
        state.components.append(pop_component(module_name, state))


def pop_component(module_name: str, state: TarjanState) -> list[str]:
    component = []
    while True:
        dependency = state.stack.pop()
        state.on_stack.remove(dependency)
        component.append(dependency)
        if dependency == module_name:
            return sorted(component)


class ImportCycleGuardTests(unittest.TestCase):
    def test_quizbank_mvp_runtime_imports_stay_acyclic(self) -> None:
        graph = runtime_import_graph(package_modules())

        cycles = [
            " -> ".join(component)
            for component in strongly_connected_components(graph)
            if len(component) > 1
        ]

        self.assertEqual(cycles, [])


if __name__ == "__main__":
    unittest.main()
