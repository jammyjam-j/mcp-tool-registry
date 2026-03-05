from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from .config import AppConfig
from .router import router as api_router
from .core.registry import ToolRegistry
from .utils.middleware import request_logging_middleware


def create_app() -> FastAPI:
    config = AppConfig()
    app = FastAPI(title=config.app_name, version=config.version)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        return await request_logging_middleware(request, call_next)

    app.add_router(api_router, prefix="/api")

    registry = ToolRegistry()
    registry.load_tools_from_package("app.tools")

    @app.get("/health", response_model=dict)
    async def health_check():
        return {"status": "ok"}

    @app.api_route("/{tool_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy_tool(tool_name: str, path: str = "", request: Request):
        tool_cls = registry.get_tool(tool_name)
        if not tool_cls:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        tool_instance = tool_cls()
        try:
            response = await tool_instance.handle(request.method, f"/{path}", request)
        except Exception as exc:
            logging.exception("Error processing tool request")
            raise HTTPException(status_code=500, detail=str(exc))
        return JSONResponse(content=response)

    @app.on_event("startup")
    async def startup():
        pass

    @app.on_event("shutdown")
    async def shutdown():
        pass

    return app


app = create_app()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)