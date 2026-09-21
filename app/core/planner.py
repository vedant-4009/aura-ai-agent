import json
from typing import Dict

from openai import OpenAI

from app.config import GROQ_API_KEY, MODEL


class Planner:
    """
    Intelligent planner for AURA.

    Uses the Groq LLM to understand the user's request
    and create a structured execution plan.
    """

    def __init__(self):
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        self.available_tools = [
            "github",
            "web",
            "files",
            "llm"
        ]

    def create_plan(self, user_input: str) -> Dict:
        prompt = f"""
You are the planning engine of an AI automation assistant called AURA.

Available tools:
- github: GitHub repositories, users, commits, issues and pull requests
- web: web pages and internet information
- files: reading and analyzing local files
- llm: general reasoning and conversation

Create a simple execution plan for the user's request.

User request:
{user_input}

Return ONLY valid JSON in this exact structure:

{{
    "goal": "short description of the goal",
    "tool": "one tool from the available tools",
    "steps": [
        "step 1",
        "step 2",
        "step 3"
    ]
}}
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AURA's planning engine. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        try:
            plan = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Planner returned invalid JSON: {content}"
            ) from exc

        if plan.get("tool") not in self.available_tools:
            plan["tool"] = "llm"

        return plan