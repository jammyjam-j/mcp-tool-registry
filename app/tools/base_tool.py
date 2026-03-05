Cannot access repo but assume sample_tool inherits BaseTool and implements run method. BaseTool should provide id, name, description, parameters schema etc. Provide validate_input, execute. Also integration with registry? maybe register decorator.

Implement:

class BaseTool(ABC):
    tool_id: str
    name: str
    description: str
    input_schema: Type[BaseModel] | None

    def __init__(self): pass

    @abstractmethod
    async def run(self, **kwargs): ...

    def validate_input(self, data: dict) -> BaseModel:
        if self.input_schema:
            return self.input_schema(**data)
        return data

Also registry register via decorator in core/decorators. Might have a decorator that registers subclass.

Implement classmethod from_registry? Use registry to get tool instance by id.

Simplify: base_tool defines __init__ registering itself in Registry (from app.core.registry import registry). On init, add to registry with self.tool_id.

Return.

Let's write.import abc
import inspect
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from app.core.registry import registry


class BaseTool(abc.ABC):
    tool_id: str
    name: str
    description: str
    input_schema: Optional[Type[BaseModel]] = None

    def __init__(self) -> None:
        if not getattr(self, "tool_id", None):
            raise ValueError("tool_id must be defined")
        registry.register_tool(self.tool_id, self)

    @abc.abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool logic."""

    def validate_input(self, data: Dict[str, Any]) -> BaseModel | Dict[str, Any]:
        if self.input_schema is None:
            return data
        try:
            return self.input_schema(**data)
        except ValidationError as exc:
            raise ValueError(f"Input validation failed for {self.tool_id}: {exc}") from exc

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "BaseTool":
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        init_kwargs = {}
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name == "self":
                continue
            if name in data:
                init_kwargs[name] = data[name]
        return cls(**init_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
        }