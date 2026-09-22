import json
from typing import Dict

from openai import OpenAI

from aura_app.config import GROQ_API_KEY, MODEL


class Planner:

    def __init__(self):

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        self.available_tools = {
            "github",
            "github_readme",
            "web",
            "files",
            "llm"
        }

    def create_plan(self, user_input: str) -> Dict:

        user_input_lower = user_input.lower()

        # --------------------------------------------------
        # DETERMINISTIC PLAN FOR GITHUB + ML REQUESTS
        # --------------------------------------------------

        if (
            "github" in user_input_lower
            and (
                "machine learning" in user_input_lower
                or "ml" in user_input_lower
            )
            and "readme" in user_input_lower
        ):

            return {
                "goal": (
                    "Find GitHub projects related to machine "
                    "learning and analyze their README files"
                ),
                "steps": [
                    {
                        "id": 1,
                        "tool": "github",
                        "task": "list repositories",
                        "depends_on": []
                    },
                    {
                        "id": 2,
                        "tool": "llm",
                        "task": (
                            "filter repositories for "
                            "machine learning topics"
                        ),
                        "depends_on": [1]
                    },
                    {
                        "id": 3,
                        "tool": "github_readme",
                        "task": (
                            "read README files of filtered "
                            "repositories"
                        ),
                        "depends_on": [2]
                    },
                    {
                        "id": 4,
                        "tool": "llm",
                        "task": (
                            "analyze README content for "
                            "project insights"
                        ),
                        "depends_on": [3]
                    }
                ]
            }

        # --------------------------------------------------
        # SIMPLE GITHUB REQUEST
        # --------------------------------------------------

        if "github" in user_input_lower:

            return {
                "goal": "Get GitHub repository information",
                "steps": [
                    {
                        "id": 1,
                        "tool": "github",
                        "task": user_input,
                        "depends_on": []
                    }
                ]
            }

        # --------------------------------------------------
        # README REQUEST
        # --------------------------------------------------

        if "readme" in user_input_lower:

            return {
                "goal": "Read and analyze a GitHub README",
                "steps": [
                    {
                        "id": 1,
                        "tool": "github_readme",
                        "task": user_input,
                        "depends_on": []
                    }
                ]
            }

        # --------------------------------------------------
        # FALLBACK TO GROQ FOR OTHER REQUESTS
        # --------------------------------------------------

        prompt = f"""
Create a very short execution plan.

User request:
{user_input}

Available tools:
github, github_readme, web, files, llm

Return ONLY JSON:

{{
  "goal": "short goal",
  "steps": [
    {{
      "id": 1,
      "tool": "llm",
      "task": "short task",
      "depends_on": []
    }}
  ]
}}

Rules:
- Maximum 3 steps.
- Use only available tools.
- Return JSON only.
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AURA's compact planning engine. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=300
        )

        choice = response.choices[0]
        content = choice.message.content

        if not content:

            raise RuntimeError(
                "Planner received an empty response from Groq. "
                f"finish_reason={choice.finish_reason}"
            )

        content = content.strip()

        if content.startswith("```"):

            content = content.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        try:

            plan = json.loads(content)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                f"Planner returned invalid JSON: {content}"
            ) from exc

        if not isinstance(
            plan.get("goal"),
            str
        ):

            raise RuntimeError(
                "Planner returned an invalid goal."
            )

        steps = plan.get("steps")

        if not isinstance(
            steps,
            list
        ) or not steps:

            raise RuntimeError(
                "Planner returned an invalid steps list."
            )

        validated_steps = []

        for index, step in enumerate(
            steps,
            start=1
        ):

            if not isinstance(
                step,
                dict
            ):

                raise RuntimeError(
                    f"Invalid planner step {index}."
                )

            tool = step.get("tool")
            task = step.get("task")

            if tool not in self.available_tools:
                tool = "llm"

            if not task:
                task = user_input

            validated_steps.append(
                {
                    "id": index,
                    "tool": tool,
                    "task": str(task).strip(),
                    "depends_on": step.get(
                        "depends_on",
                        []
                    )
                }
            )

        return {
            "goal": plan["goal"].strip(),
            "steps": validated_steps
        }