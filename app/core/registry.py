import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type

from app.tools.base_tool import BaseTool


class ToolNotFoundError(Exception):
    pass


class DuplicateToolNameError(Exception):
    pass


class Registry:
    _instance = None

    def __new__(cls) -> "Registry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Type[BaseTool]] = {}
        return cls._instance

    @property
    def tools(self) -> Dict[str, Type[BaseTool]]:
        return self._tools

    def register(self, tool_cls: Type[BaseTool]) -> None:
        name = getattr(tool_cls, "name", None)
        if not isinstance(name, str):
            raise ValueError(f"Tool class {tool_cls.__qualname__} must define a string 'name' attribute")
        if name in self._tools:
            raise DuplicateToolNameError(f"Duplicate tool name: {name}")
        self._tools[name] = tool_cls

    def unregister(self, name: str) -> None:
        try:
            del self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(name) from exc

    def get_tool(self, name: str) -> Type[BaseTool]:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(name) from exc

    def list_tools(self) -> Dict[str, Type[BaseTool]]:
        return dict(self._tools)

    def discover_and_register_all(self) -> None:
        package_path = Path(importlib.import_module("app.tools").__file__).parent
        for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            if module_name == "__init__":
                continue
            module_fullname = f"app.tools.{module_name}"
            try:
                module = importlib.import_module(module_fullname)
            except Exception:
                continue
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                ):
                    self.register(attr)


def get_registry() -> Registry:
    registry = Registry()
    if not registry.tools:
        registry.discover_and_register_all()
    return registry

# Expose public API
__all__ = ["Registry", "get_registry", "ToolNotFoundError", "DuplicateToolNameError"]