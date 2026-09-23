import json
import re
from typing import Dict
from openai import OpenAI
from aura_app.config import GROQ_API_KEY, MODEL

class Planner:
    def __init__(self):
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
        self.client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        self.available_tools = {"github", "github_readme", "web_search", "web", "files", "file_read", "llm"}

    def _validate(self, plan: Dict, user_input: str) -> Dict:
        if not isinstance(plan, dict) or not isinstance(plan.get("goal"), str):
            raise RuntimeError("Planner returned an invalid plan.")
        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps:
            raise RuntimeError("Planner returned an invalid steps list.")
        out = []
        for i, step in enumerate(steps[:4], 1):
            if not isinstance(step, dict):
                raise RuntimeError(f"Invalid planner step {i}.")
            tool = step.get("tool")
            if tool not in self.available_tools:
                raise RuntimeError(f"Planner selected unsupported tool: {tool}")
            out.append({"id": i, "tool": tool, "task": str(step.get("task") or user_input).strip(), "depends_on": step.get("depends_on", []) if isinstance(step.get("depends_on", []), list) else []})
        return {"goal": plan["goal"].strip(), "steps": out}

    def create_plan(self, user_input: str) -> Dict:
        text = user_input.strip()
        lower = text.lower()
        if not text:
            raise RuntimeError("User request cannot be empty.")

        # Deterministic GitHub repository listing.
        if "github" in lower and ("list my" in lower or "show my" in lower) and ("repo" in lower or "repositories" in lower):
            return {"goal": "List the user GitHub repositories.", "steps": [{"id": 1, "tool": "github", "task": "list repositories", "depends_on": []}]}

        # Deterministic ML-project analysis: GitHub -> LLM filter -> README -> LLM summary.
        is_ml = bool(re.search(r"\bml\b|machine learning|deep learning|computer vision|predictive modeling", lower))
        is_github_project = "github" in lower and any(x in lower for x in ("project", "projects", "repo", "repository", "repositories", "analyze", "analysis"))
        if is_ml and is_github_project:
            return {"goal": "Find and analyze the user GitHub machine-learning projects.", "steps": [
                {"id": 1, "tool": "github", "task": "list repositories", "depends_on": []},
                {"id": 2, "tool": "llm", "task": "From the previous GitHub repository result, identify repositories related to ML, AI, deep learning, computer vision, or predictive modeling. Return only repository names.", "depends_on": [1]},
                {"id": 3, "tool": "github_readme", "task": "read README files for the filtered repositories", "depends_on": [2]},
                {"id": 4, "tool": "llm", "task": "Analyze the README results and summarize each ML project, including purpose, technologies, and notable points.", "depends_on": [3]}
            ]}

        if "github" in lower and "readme" in lower:
            return {"goal": "Read and analyze a GitHub README.", "steps": [{"id": 1, "tool": "github_readme", "task": text, "depends_on": []}]}

        if "github" in lower:
            return {"goal": "Get GitHub repository information.", "steps": [{"id": 1, "tool": "github", "task": text, "depends_on": []}]}

        if any(re.search(p, lower) for p in (r"\blatest\b", r"\bcurrent\b", r"\brecent\b", r"search the web", r"search online", r"search the internet", r"look up online")):
            return {"goal": "Search the public web and summarize the results.", "steps": [{"id": 1, "tool": "web_search", "task": text, "depends_on": []}]}

        prompt = f"""Create a valid execution plan for this request:

{text}

Available tools: github, github_readme, web_search, web, files, file_read, llm
Return ONLY JSON with keys goal and steps. Maximum 4 steps. Each step must contain id, tool, task, depends_on. Use only available tools."""
        response = self.client.chat.completions.create(model=MODEL, messages=[
            {"role": "system", "content": "You are AURA execution planner. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ], temperature=0, max_tokens=500)
        content = (response.choices[0].message.content or "").strip()
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE).strip()
        if not content:
            raise RuntimeError("Planner received an empty response from Groq.")
        try:
            plan = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Planner returned invalid JSON: {content}") from exc
        return self._validate(plan, text)