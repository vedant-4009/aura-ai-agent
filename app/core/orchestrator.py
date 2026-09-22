from typing import Dict, Any

from openai import OpenAI

from app.config import GROQ_API_KEY, MODEL
from app.core.planner import Planner
from app.core.executor import Executor
from app.core.tool_registry import get_tools


class Orchestrator:

    def __init__(self):

        self.planner = Planner()
        self.executor = Executor(get_tools())

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

    def compact_execution(
        self,
        execution: Dict[str, Any]
    ):

        compact_results = {}

        for step_id, result in execution.get(
            "results",
            {}
        ).items():

            item = {
                "success": result.get("success"),
                "tool": result.get("tool"),
                "task": result.get("task")
            }

            if not result.get("success"):

                item["error"] = result.get("error")
                compact_results[step_id] = item
                continue

            data = result.get("result")

            if isinstance(data, dict):

                compact_data = {}

                for key, value in data.items():

                    compact_data[key] = str(value)[:3000]

                item["result"] = compact_data

            elif isinstance(data, str):

                item["result"] = data[:5000]

            else:

                item["result"] = data

            compact_results[step_id] = item

        return {
            "success": execution.get("success"),
            "goal": execution.get("goal"),
            "results": compact_results
        }

    def generate_final_response(
        self,
        user_input: str,
        plan: Dict[str, Any],
        execution: Dict[str, Any]
    ) -> str:

        compact_execution = self.compact_execution(
            execution
        )

        prompt = f"""
You are AURA, a professional AI automation assistant.

User request:
{user_input}

Execution plan:
{plan}

Execution results:
{compact_execution}

Answer the user's request using ONLY the execution results.

Rules:
- Never invent information.
- Never claim a failed step succeeded.
- Never say you manually performed an action.
- If a step failed, clearly mention the failure.
- Do not expose API keys, tokens, or credentials.
- Keep the answer concise and useful.
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are AURA's final response engine."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=700
        )

        content = response.choices[0].message.content

        if not content:
            return "AURA could not generate a final response."

        return content.strip()

    def run(
        self,
        user_input: str
    ) -> Dict[str, Any]:

        plan = self.planner.create_plan(
            user_input
        )

        execution = self.executor.execute(
            plan
        )

        response = self.generate_final_response(
            user_input,
            plan,
            execution
        )

        return {
            "input": user_input,
            "plan": plan,
            "execution": execution,
            "response": response
        }