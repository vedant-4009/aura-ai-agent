from typing import Dict, Any

from openai import OpenAI

from app.config import GROQ_API_KEY, MODEL
from app.core.planner import Planner
from app.core.executor import Executor
from app.core.tool_registry import get_tools


class Orchestrator:
    """
    Coordinates planning, tool execution, and final response generation.
    """

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor(get_tools())

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

    def generate_final_response(
        self,
        user_input: str,
        plan: Dict[str, Any],
        execution: Dict[str, Any]
    ) -> str:

        prompt = f"""
You are AURA, a professional AI automation assistant.

The user asked:
{user_input}

AURA created this plan:
{plan}

The tool execution produced:
{execution}

Using the tool result, provide a clear and useful answer to the user.

Rules:
- Do not mention internal implementation details unless necessary.
- Do not invent information.
- Use the actual tool result.
- Be concise but helpful.
- If the tool failed, clearly explain the problem.
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are AURA, an AI automation assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    def run(self, user_input: str) -> Dict[str, Any]:

        # 1. Create plan
        plan = self.planner.create_plan(user_input)

        # 2. Execute selected tool
        execution = self.executor.execute(plan)

        # 3. Generate final response
        final_response = self.generate_final_response(
            user_input,
            plan,
            execution
        )

        return {
            "input": user_input,
            "plan": plan,
            "execution": execution,
            "response": final_response
        }