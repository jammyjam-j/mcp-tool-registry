from functools import wraps
from typing import Any, Callable, Optional, Type

from .registry import ToolRegistry


class RegistrationError(RuntimeError):
    pass


def register_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable[[Type[Any]], Type[Any]]:
    def decorator(cls: Type[Any]) -> Type[Any]:
        tool_name = name or cls.__name__
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise RegistrationError("Tool name must be a non-empty string")
        registry = ToolRegistry.instance()
        if registry.is_registered(tool_name):
            raise RegistrationError(f"Tool '{tool_name}' is already registered")
        setattr(cls, "_tool_name", tool_name)
        setattr(cls, "_tool_description", description or "")
        registry.register_tool(tool_name, cls)
        return cls

    return decorator


def route_endpoint(
    path: str,
    methods: Optional[list[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not isinstance(path, str) or not path.startswith("/"):
            raise RegistrationError("Path must be a string starting with '/'")
        allowed_methods = [m.upper() for m in (methods or ["GET"])]
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        setattr(wrapper, "_route_path", path)
        setattr(wrapper, "_route_methods", allowed_methods)
        return wrapper

    return decorator