# mcp‑tool‑registry  
Dynamic MCP tool registry with auto‑discovery and request routing via FastAPI  

---

## Overview  
mcp-tool-registry is a lightweight service that discovers, registers, and routes requests to Model Context Protocol (MCP) tools at runtime. It eliminates hard‑coded agent configurations by scanning the `app/tools` package for subclasses of `BaseTool`, exposing them through a RESTful API, and forwarding MCP calls to the appropriate implementation.  

---

## Features  
- **Auto‑discovery** – New tools added to `app/tools/` are automatically registered on startup.  
- **FastAPI integration** – Exposes a clean HTTP interface (`GET /tools`, `POST /tools/{name}`) for listing and invoking tools.  
- **Request routing** – Incoming MCP requests are forwarded to the correct tool based on the tool name in the path.  
- **Middleware logging & validation** – Custom middleware captures request metadata and validates payloads against Pydantic schemas.  
- **Docker support** – Ready‑to‑run Dockerfile and docker‑compose stack for local or CI deployment.  
- **Testing harness** – Unit tests cover registry logic, tool discovery, and endpoint behavior.  

---

## Tech Stack  
| Layer | Technology |
|-------|------------|
| Web framework | FastAPI (Starlette) |
| Dependency injection & settings | Pydantic / `app/settings.py` |
| Database | SQLite (via SQLAlchemy in `app/database/db.py`) |
| Testing | pytest, httpx |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |
| Containerization | Docker, docker‑compose |

---

## Installation  

```bash
# Clone the repository
git clone https://github.com/jammyjam-j/mcp-tool-registry

cd mcp-tool-registry

# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### Docker  

```bash
docker build -t mcp-tool-registry .
docker run -p 8000:80 --name mcp-tool-registry mcp-tool-registry
```

Or start the full stack with Compose:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

---

## Usage Examples  

### Listing Available Tools  

```bash
curl http://localhost:8000/tools
```

Response:

```json
{
  "tools": [
    {
      "name": "sample_tool",
      "description": "A simple example tool."
    }
  ]
}
```

### Invoking a Tool  

```bash
curl -X POST http://localhost:8000/tools/sample_tool \
     -H "Content-Type: application/json" \
     -d '{"input":"Hello, MCP!"}'
```

Response:

```json
{
  "output": "SampleTool processed: Hello, MCP!"
}
```

### Using the Python Client  

```python
import httpx

async def call_tool(name: str, payload: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:8000/tools/{name}", json=payload)
        return resp.json()

# Example
result = await call_tool("sample_tool", {"input": "test"})
print(result["output"])
```

---

## API Endpoints  

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tools` | Retrieve a list of registered tools. |
| `POST` | `/tools/{name}` | Execute the tool identified by `{name}` with a JSON body conforming to its input schema. |

All responses are JSON and follow the Pydantic models defined in `app/models/tool_model.py`.

---

## References and Resources  

- [DockerMCPGateway: Dynamic Discovery & Execution](https://talkin.icu/blog/docker-mcp-gateway-dynamic-discovery)  
- [GitHub - toolsdk-ai/toolsdk-mcp-registry](https://github.com/toolsdk-ai/toolsdk-mcp-registry)  
- [The MissingMCPPlaybook: Deploying Custom Agents on Claude.ai…](https://freedium-mirror.cfd/05274f60a970)  
- [RouterMCPServer by Adam Wattis | PulseMCP](https://www.pulsemcp.com/servers/adamwattis-router)  
- [Build an MCP server – Model Context Protocol](https://modelcontextprotocol.io/docs/develop/build-server)  

---

## Contributing  

1. Fork the repository at https://github.com/jammyjam-j/mcp-tool-registry  
2. Create a feature branch (`git checkout -b feature/your-feature`)  
3. Run tests locally: `pytest`  
4. Commit your changes and push to your fork  
5. Open a pull request against the main branch of the upstream repository  

Issues can be reported at https://github.com/jammyjam-j/mcp-tool-registry/issues.

---

## License  

MIT © 2026

---