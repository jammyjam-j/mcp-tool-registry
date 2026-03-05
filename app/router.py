from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any

from app.core.registry import ToolRegistry
from app.schemas.tool_schema import ToolSchema
from app.tools.base_tool import BaseTool


router = APIRouter()


def get_registry() -> ToolRegistry:
    return ToolRegistry.instance()


@router.get("/tools", response_model=List[str])
async def list_tools(registry: ToolRegistry = Depends(get_registry)):
    return registry.list_tools()


@router.get("/tools/{tool_name}", response_model=ToolSchema)
async def get_tool(
    tool_name: str,
    registry: ToolRegistry = Depends(get_registry),
):
    tool: BaseTool | None = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolSchema.from_orm(tool)


@router.post("/tools/{tool_name}/run", response_model=Dict[str, Any])
async def run_tool(
    tool_name: str,
    payload: Dict[str, Any] = Body(...),
    registry: ToolRegistry = Depends(get_registry),
):
    tool: BaseTool | None = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    try:
        result = await tool.run(**payload)
    except TypeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid parameters: {exc}",
        )
    return {"result": result}