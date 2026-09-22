from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from aura_app.core.orchestrator import Orchestrator


app = FastAPI(
    title="AURA AI Agent",
    description="AI Automation Assistant",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    message: str


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>AURA — AI Automation Assistant</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: Arial, sans-serif;
            background: #080b12;
            color: #f5f7fb;
            min-height: 100vh;
        }

        .container {
            max-width: 1000px;
            margin: auto;
            padding: 40px 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 35px;
        }

        .logo {
            font-size: 48px;
            font-weight: 800;
            letter-spacing: 4px;
        }

        .subtitle {
            margin-top: 8px;
            color: #9ca3af;
            font-size: 16px;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 15px;
            padding: 7px 13px;
            border: 1px solid #263044;
            border-radius: 20px;
            color: #a7f3d0;
            font-size: 13px;
            background: #101722;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
        }

        .card {
            background: #10141d;
            border: 1px solid #252c3a;
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.25);
        }

        textarea {
            width: 100%;
            min-height: 130px;
            resize: vertical;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #303848;
            background: #0b0f17;
            color: white;
            font-size: 15px;
            outline: none;
        }

        textarea:focus {
            border-color: #6366f1;
        }

        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            gap: 15px;
        }

        .hint {
            color: #71798a;
            font-size: 13px;
        }

        button {
            border: none;
            border-radius: 10px;
            padding: 12px 22px;
            background: #6366f1;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }

        button:hover {
            background: #5558e8;
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            margin-top: 25px;
            padding: 15px;
            border-radius: 12px;
            background: #0d1420;
            color: #a5b4fc;
        }

        .response {
            display: none;
            margin-top: 25px;
        }

        .response h2 {
            font-size: 18px;
            margin-bottom: 12px;
        }

        .result {
            white-space: pre-wrap;
            line-height: 1.7;
            color: #d8dce5;
            background: #0b0f17;
            border: 1px solid #252c3a;
            border-radius: 12px;
            padding: 18px;
        }

        .error {
            color: #fca5a5;
        }

        .examples {
            margin-top: 18px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .example {
            border: 1px solid #2c3444;
            background: #0d121b;
            color: #9ca3af;
            border-radius: 8px;
            padding: 8px 11px;
            cursor: pointer;
            font-size: 12px;
        }

        .example:hover {
            color: white;
            border-color: #6366f1;
        }

        footer {
            text-align: center;
            color: #5f6878;
            font-size: 12px;
            margin-top: 30px;
        }

        @media (max-width: 600px) {
            .container {
                padding: 25px 14px;
            }

            .logo {
                font-size: 38px;
            }

            .actions {
                flex-direction: column;
                align-items: stretch;
            }

            button {
                width: 100%;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <div class="logo">AURA</div>

        <div class="subtitle">
            AI Automation Assistant
        </div>

        <div class="status">
            <span class="dot"></span>
            System Online
        </div>
    </div>

    <div class="card">

        <textarea
            id="message"
            placeholder="Ask AURA to perform a task..."
        ></textarea>

        <div class="examples">
            <div class="example" onclick="setExample(
                'Find my GitHub projects related to machine learning and analyze their README files'
            )">
                Analyze my ML GitHub projects
            </div>

            <div class="example" onclick="setExample(
                'List my GitHub repositories'
            )">
                List my GitHub repositories
            </div>
        </div>

        <div class="actions">

            <div class="hint">
                AURA can plan and execute multi-step tasks.
            </div>

            <button id="runButton" onclick="runAURA()">
                Run AURA
            </button>

        </div>

        <div id="loading" class="loading">
            AURA is thinking and executing your request...
        </div>

        <div id="response" class="response">

            <h2>Response</h2>

            <div id="result" class="result"></div>

        </div>

    </div>

    <footer>
        AURA • Python • FastAPI • Groq • GitHub
    </footer>

</div>


<script>

function setExample(text) {
    document.getElementById("message").value = text;
}


async function runAURA() {

    const message =
        document.getElementById("message").value.trim();

    const button =
        document.getElementById("runButton");

    const loading =
        document.getElementById("loading");

    const responseBox =
        document.getElementById("response");

    const result =
        document.getElementById("result");


    if (!message) {

        result.textContent =
            "Please enter a request.";

        result.classList.add("error");

        responseBox.style.display = "block";

        return;
    }


    button.disabled = true;

    loading.style.display = "block";

    responseBox.style.display = "none";

    result.classList.remove("error");


    try {

        const response = await fetch(
            "/api/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        const data = await response.json();


        if (data.success) {

            result.textContent =
                data.response || "No response generated.";

        } else {

            result.textContent =
                data.error || "Something went wrong.";

            result.classList.add("error");
        }


        responseBox.style.display = "block";


    } catch (error) {

        result.textContent =
            "Unable to connect to AURA backend.";

        result.classList.add("error");

        responseBox.style.display = "block";
    }


    loading.style.display = "none";

    button.disabled = false;
}

</script>

</body>
</html>
"""


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