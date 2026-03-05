from importlib import import_module
import pkgutil
from typing import Dict, Type

from .base_tool import BaseTool


class ToolRegistry:
    def __init__(self):
        self._registry: Dict[str, Type[BaseTool]] = {}

    def register(self, tool_cls: Type[BaseTool]) -> Type[BaseTool]:
        name = getattr(tool_cls, "name", None)
        if not isinstance(name, str) or not name:
            raise ValueError(f"Tool class {tool_cls.__name__} must define a non-empty 'name' attribute.")
        if name in self._registry:
            existing = self._registry[name]
            raise ValueError(
                f"Duplicate tool registration for '{name}'. Existing: {existing.__module__}.{existing.__qualname__}, "
                f"Attempted: {tool_cls.__module__}.{tool_cls.__qualname__}"
            )
        self._registry[name] = tool_cls
        return tool_cls

    def get(self, name: str) -> Type[BaseTool]:
        try:
            return self._registry[name]
        except KeyError as exc:
            raise KeyError(f"Tool '{name}' not found in registry.") from exc

    def all_tools(self) -> Dict[str, Type[BaseTool]]:
        return dict(self._registry)


_registry = ToolRegistry()


def load_all_tools() -> None:
    package = __package__
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if module_name == "__init__":
            continue
        import_module(f"{package}.{module_name}")


register_tool = _registry.register


load_all_tools()
__all__ = [
    "BaseTool",
    "register_tool",
    "_registry",
]