We don't have file contents but we can assume base_tool defines ToolBase with run method. Sample tool maybe has execute that returns something.

Test registry registration, tool discovery, usage via FastAPI? But test_tools should test tool logic and integration.

We'll create tests for:

- Instantiating sample_tool
- Running it
- Checking attributes from schema
- Testing error handling when missing required args

Use pytest fixtures: app fixture already maybe in conftest. We'll use TestClient to call API endpoints? router likely has endpoint /tools/{name}/run.

Let's inspect router.import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.registry import registry
from app.tools.sample_tool import SampleTool
from app.schemas.tool_schema import ToolSchema


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_sample_tool_registration():
    tool_name = "sample"
    assert tool_name in registry._tools, f"{tool_name} not registered"
    tool_cls = registry.get(tool_name)
    assert issubclass(tool_cls, SampleTool), f"{tool_name} is not a subclass of SampleTool"


def test_sample_tool_run_success(client: TestClient):
    payload = {"input_data": "test"}
    response = client.post("/tools/sample/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["output"] == f"Processed {payload['input_data']}"


def test_sample_tool_missing_input(client: TestClient):
    payload = {}
    response = client.post("/tools/sample/run", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"][-1] == "input_data" for err in errors)


def test_tool_schema_serialization():
    schema_dict = {
        "name": "sample",
        "description": "A sample tool that echoes input.",
        "parameters": {"type": "object", "properties": {"input_data": {"type": "string"}}},
        "returns": {"type": "object"},
    }
    schema = ToolSchema(**schema_dict)
    assert schema.name == "sample"
    assert schema.description == schema_dict["description"]
    assert "input_data" in schema.parameters["properties"]


def test_registry_unregistration_and_reregistration():
    tool_name = "sample"
    registry.unregister(tool_name)
    assert tool_name not in registry._tools
    registry.register(SampleTool)
    assert tool_name in registry._tools
    registry.unregister(tool_name)


def test_tool_file_exists(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("tools")
    sample_file = Path(tmp_dir) / "sample_tool.py"
    sample_file.write_text(
        """
from app.tools.base_tool import ToolBase

class SampleTool(ToolBase):
    name = "sample"

    def run(self, input_data: str) -> dict:
        return {"output": f"Processed {input_data}"}
"""
    )
    assert sample_file.exists()
    # Ensure that importing this file does not raise errors
    import importlib.util

    spec = importlib.util.spec_from_file_location("sample_tool", str(sample_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "SampleTool")
    assert issubclass(module.SampleTool, object)


def test_registry_duplicate_registration():
    with pytest.raises(ValueError):
        registry.register(SampleTool)

def test_tool_run_with_additional_params(client: TestClient):
    payload = {"input_data": "hello", "extra": 123}
    response = client.post("/tools/sample/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == f"Processed {payload['input_data']}"
    # The tool should ignore unexpected fields

def test_tool_run_error_handling(client: TestClient):
    payload = {"input_data": None}
    response = client.post("/tools/sample/run", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"][-1] == "input_data" for err in errors)

def test_tool_schema_validation():
    with pytest.raises(ValueError):
        ToolSchema(name="invalid-tool!", description="bad", parameters={}, returns={})
    schema_dict = {
        "name": "validtool",
        "description": "ok",
        "parameters": {"type": "object"},
        "returns": {"type": "object"},
    }
    schema = ToolSchema(**schema_dict)
    assert schema.name == "validtool"

def test_registry_get_nonexistent():
    with pytest.raises(KeyError):
        registry.get("nonexistent")

def test_tool_run_output_type(client: TestClient):
    payload = {"input_data": "data"}
    response = client.post("/tools/sample/run", json=payload)
    assert isinstance(response.json()["output"], str)

def test_registry_thread_safety():
    import threading

    def register_and_unregister():
        registry.register(SampleTool)
        registry.unregister("sample")

    threads = [threading.Thread(target=register_and_unregister) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert "sample" not in registry._tools

def test_tool_schema_missing_fields():
    with pytest.raises(ValueError):
        ToolSchema(name="tool", description=None, parameters={}, returns={})

def test_sample_tool_run_with_invalid_type(client: TestClient):
    payload = {"input_data": 123}
    response = client.post("/tools/sample/run", json=payload)
    assert response.status_code == 422

def test_registry_register_custom_tool(tmp_path_factory):
    custom_file = tmp_path_factory.mktemp("custom") / "mytool.py"
    custom_file.write_text(
        """
from app.tools.base_tool import ToolBase

class MyTool(ToolBase):
    name = "mytool"

    def run(self, value: int) -> dict:
        return {"output": value * 2}
"""
    )
    spec = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mytool", str(custom_file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        registry.register(module.MyTool)
        assert "mytool" in registry._tools
        client = TestClient(app)
        response = client.post("/tools/mytool/run", json={"value": 5})
        assert response.json()["output"] == 10
    finally:
        if spec and hasattr(spec.loader, "exec_module"):
            pass
        registry.unregister("mytool")