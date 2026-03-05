We don't have content but assume it defines BaseTool with run method, name property etc. We'll create SampleTool subclass implementing a simple operation: maybe echo or math addition.

Need integration with registry: register via decorator? decorators.py likely contains @register_tool.

We'll write sample tool with input schema and output schema using pydantic models from schemas/tool_schema? Let's inspect those files quickly mentally: tool_model, tool_schema. Probably define ToolModel with name, description etc. For sample tool we need to expose a FastAPI route via router? But tools are used by registry for routing.

Simplify: implement SampleTool with method execute that takes dict and returns dict.

Also provide metadata attributes like name, description, version.

Implement validation using pydantic BaseModel.

Ok produce code.import json
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError

from app.core.registry import register_tool
from app.tools.base_tool import BaseTool


class SampleInput(BaseModel):
    numbers: list[int] = Field(..., min_items=1)
    operation: str = Field(
        ...,
        regex="^(add|subtract|multiply|divide)$",
        description="Operation to perform on the numbers.",
    )


class SampleOutput(BaseModel):
    result: Any
    details: Dict[str, Any]


@register_tool
class SampleTool(BaseTool):
    name: str = "sample-tool"
    version: str = "1.0.0"
    description: str = (
        "Performs basic arithmetic operations on a list of integers."
    )
    author: str = "https://github.com/jammyjam-j/mcp-tool-registry"

    def validate_input(self, payload: Dict[str, Any]) -> SampleInput:
        try:
            return SampleInput(**payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid input data: {exc}") from exc

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        validated = self.validate_input(payload)
        numbers = validated.numbers
        operation = validated.operation.lower()

        if operation == "add":
            result = sum(numbers)
        elif operation == "subtract":
            result = numbers[0] - sum(numbers[1:])
        elif operation == "multiply":
            prod = 1
            for n in numbers:
                prod *= n
            result = prod
        else:  # divide
            try:
                result = numbers[0]
                for n in numbers[1:]:
                    result /= n
            except ZeroDivisionError as exc:
                raise ValueError("Division by zero encountered") from exc

        output = SampleOutput(result=result, details={"operation": operation})
        return json.loads(output.json())

    def get_schema(self) -> Dict[str, Any]:
        return {
            "input": SampleInput.schema(),
            "output": SampleOutput.schema(),
        }