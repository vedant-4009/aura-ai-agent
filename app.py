from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.index import HTML_PAGE, ChatRequest
from aura_app.core.orchestrator import Orchestrator

app = FastAPI(
    title="AURA AI Agent",
    description="AI Automation Assistant",
    version="1.0.0"
)


@app.get("/", response_class=HTMLResponse)
def root():
    return HTML_PAGE


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AURA"
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        return {
            "success": False,
            "error": "Message cannot be empty."
        }

    try:
        aura = Orchestrator()
        result = aura.run(message)

        return {
            "success": True,
            "response": result.get("response"),
            "plan": result.get("plan"),
            "execution": result.get("execution")
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }
