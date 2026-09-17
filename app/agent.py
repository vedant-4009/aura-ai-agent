from openai import OpenAI
import json

from app.config import GROQ_API_KEY, MODEL
from app.tools.files import list_files, read_file
from app.tools.web import fetch_webpage
from app.tools.github import github_user


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Add it to your .env file."
    )


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a local directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "The folder path to list."
                    }
                },
                "required": ["folder"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local UTF-8 text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to read."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "Fetch and extract readable text from a public webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The public webpage URL."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_user",
            "description": "Get public information about a GitHub user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The GitHub username."
                    }
                },
                "required": ["username"]
            }
        }
    }
]


SYSTEM_PROMPT = """
You are a practical AI automation agent.

You can use tools to:
- Inspect local files
- Read local text files
- Fetch public webpages
- Get public GitHub user information

Use a tool when it is actually needed.

Do not claim that an action was completed unless the tool result confirms it.

If a tool fails, clearly explain the problem.

Keep responses clear, useful, and concise.
"""


def run_agent(user_message: str) -> str:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    for _ in range(5):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message

        messages.append(message)

        if not message.tool_calls:
            return message.content or "No response."

        for tool_call in message.tool_calls:

            name = tool_call.function.name

            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result = "Invalid tool arguments."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

                continue

            if name == "list_files":
                result = list_files(**args)

            elif name == "read_file":
                result = read_file(**args)

            elif name == "fetch_webpage":
                result = fetch_webpage(**args)

            elif name == "github_user":
                result = github_user(**args)

            else:
                result = f"Unknown tool: {name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

    return "The agent reached its tool-call limit."