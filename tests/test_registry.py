import pytest
from fastapi import FastAPI
from app.core.registry import Registry, ToolNotFoundError
from app.tools.sample_tool import SampleTool

@pytest.fixture(scope="module")
def registry() -> Registry:
    return Registry()

def test_register_and_retrieve_tool(registry: Registry):
    tool_name = "sample"
    instance = SampleTool()
    registry.register_tool(tool_name, instance)
    retrieved = registry.get_tool(tool_name)
    assert isinstance(retrieved, SampleTool)

def test_duplicate_registration_raises(registry: Registry):
    tool_name = "duplicate"
    instance1 = SampleTool()
    instance2 = SampleTool()
    registry.register_tool(tool_name, instance1)
    with pytest.raises(ValueError):
        registry.register_tool(tool_name, instance2)

def test_get_nonexistent_tool_raises(registry: Registry):
    with pytest.raises(ToolNotFoundError):
        registry.get_tool("nonexistent")

def test_list_tools_returns_all_registered(registry: Registry):
    names = {"alpha", "beta"}
    for name in names:
        registry.register_tool(name, SampleTool())
    listed_names = set(registry.list_tools())
    assert names.issubset(listed_names)

def test_registry_with_fastapi_application():
    app = FastAPI()
    registry = Registry()
    tool_name = "fastapi_tool"
    instance = SampleTool()
    registry.register_tool(tool_name, instance)
    @app.get(f"/{tool_name}")
    def use_tool():
        return {"status": "ok"}
    client_app = app.test_client() if hasattr(app, "test_client") else None
    assert client_app is not None

def test_registry_auto_discovery(monkeypatch: pytest.MonkeyPatch):
    import pkgutil
    discovered_tools = []
    def fake_iter_modules(path=None, prefix=""):
        return [pkgutil.ModuleInfo(name="sample_tool", loader=None, is_pkg=False)]
    monkeypatch.setattr(pkgutil, "iter_modules", fake_iter_modules)
    registry = Registry()
    registry.auto_discover_tools("app.tools")
    assert any(tool.name == "SampleTool" for tool in registry.list_tools())

def test_registry_thread_safety(registry: Registry):
    import threading
    def register_and_retrieve(name):
        registry.register_tool(name, SampleTool())
        return registry.get_tool(name)
    threads = [threading.Thread(target=register_and_retrieve, args=(f"name_{i}",)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(registry.list_tools()) >= 10

def test_registry_remove_tool_if_exists():
    registry = Registry()
    name = "to_remove"
    instance = SampleTool()
    registry.register_tool(name, instance)
    registry.remove_tool(name)
    with pytest.raises(ToolNotFoundError):
        registry.get_tool(name)

def test_registry_register_with_invalid_name(registry: Registry):
    with pytest.raises(TypeError):
        registry.register_tool(123, SampleTool())

def test_registry_register_with_none_instance(registry: Registry):
    with pytest.raises(ValueError):
        registry.register_tool("none", None)