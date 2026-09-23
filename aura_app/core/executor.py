import json
from typing import Dict, Any, Callable

from openai import OpenAI

from aura_app.config import GROQ_API_KEY, MODEL
from aura_app.core.security import SecurityManager


class Executor:

    def __init__(self, tools: Dict[str, Callable]):

        self.tools = tools
        self.security = SecurityManager()

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

    # --------------------------------------------------
    # MAIN EXECUTION
    # --------------------------------------------------

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:

        if not plan.get("steps"):
            return {
                "success": False,
                "goal": plan.get("goal"),
                "error": "No execution steps found."
            }

        return self.execute_steps(plan)

    # --------------------------------------------------
    # MULTI-STEP EXECUTION
    # --------------------------------------------------

    def execute_steps(
        self,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:

        results = {}

        for step in plan["steps"]:

            step_id = str(step["id"])
            tool_name = step.get("tool")
            task = step.get("task", "")
            dependencies = step.get("depends_on", [])

            previous_results = []

            for dependency_id in dependencies:

                dependency = results.get(
                    str(dependency_id)
                )

                if dependency:
                    previous_results.append(
                        dependency
                    )

            # Security check
            security = self.security.check(
                tool_name
            )

            if not security["allowed"]:

                results[step_id] = {
                    "success": False,
                    "tool": tool_name,
                    "task": task,
                    "error": security["reason"]
                }

                continue

            try:

                # LLM step
                if tool_name == "llm":

                    # README analysis
                    if self.is_readme_analysis(
                        previous_results
                    ):

                        result = self.analyze_readmes(
                            previous_results
                        )

                    # Repository filtering
                    elif self.is_repository_filter(
                        task
                    ):

                        result = self.run_llm(
                            task,
                            previous_results,
                            structured=True
                        )

                    # Normal LLM reasoning
                    else:

                        result = self.run_llm(
                            task,
                            previous_results,
                            structured=False
                        )

                # Other tools
                else:

                    result = self.run_tool(
                        tool_name,
                        task,
                        previous_results
                    )

                results[step_id] = {
                    "success": True,
                    "tool": tool_name,
                    "task": task,
                    "result": result
                }

            except Exception as exc:

                results[step_id] = {
                    "success": False,
                    "tool": tool_name,
                    "task": task,
                    "error": str(exc)
                }

        overall_success = all(
            item.get("success", False)
            for item in results.values()
        )

        return {
            "success": overall_success,
            "goal": plan.get("goal"),
            "results": results
        }

    # --------------------------------------------------
    # TOOL RUNNER
    # --------------------------------------------------

    def run_tool(
        self,
        tool_name: str,
        task: str,
        previous_results: list
    ):

        tool = self.tools.get(tool_name)

        if not tool:
            raise RuntimeError(
                f"Tool '{tool_name}' is not registered."
            )

        if tool_name == "github_readme":

            return self.run_github_readme(
                tool,
                previous_results,
                task
            )

        return tool(task)

    # --------------------------------------------------
    # GITHUB README FETCHER
    # --------------------------------------------------

    def run_github_readme(
        self,
        tool: Callable,
        previous_results: list,
        task: str = ""
    ):

        repository_names = (
            self.extract_repository_names(
                previous_results
            )
        )

        if not repository_names and task:
            from aura_app.tools.github import extract_repo_names
            repository_names = extract_repo_names(task)

        if not repository_names:

            return {
                "error": "No repository names were found."
            }

        readmes = {}

        for repo_name in repository_names:

            try:

                readmes[repo_name] = tool(
                    repo_name
                )

            except Exception as exc:

                readmes[repo_name] = (
                    f"README fetch failed: {exc}"
                )

        return readmes

    # --------------------------------------------------
    # EXTRACT REPOSITORY NAMES
    # --------------------------------------------------

    def extract_repository_names(
        self,
        previous_results: list
    ) -> list[str]:

        names = []

        for item in previous_results:

            result = item.get("result")

            if not isinstance(result, str):
                continue

            try:

                data = json.loads(result)

            except json.JSONDecodeError:

                continue

            repositories = data.get(
                "repositories",
                []
            )

            if not isinstance(
                repositories,
                list
            ):
                continue

            for repo_name in repositories:

                if isinstance(
                    repo_name,
                    str
                ):

                    repo_name = repo_name.strip()

                    if (
                        repo_name
                        and repo_name not in names
                    ):

                        names.append(
                            repo_name
                        )

        return names

    # --------------------------------------------------
    # REPOSITORY FILTER DETECTION
    # --------------------------------------------------

    def is_repository_filter(
        self,
        task: str
    ) -> bool:

        task_lower = task.lower()

        keywords = [
            "repository",
            "repositories",
            "github projects",
            "repo",
            "machine learning"
        ]

        return any(
            keyword in task_lower
            for keyword in keywords
        )

    # --------------------------------------------------
    # README ANALYSIS DETECTION
    # --------------------------------------------------

    def is_readme_analysis(
        self,
        previous_results: list
    ) -> bool:

        for item in previous_results:

            result = item.get("result")

            if (
                isinstance(result, dict)
                and result
            ):

                if any(
                    isinstance(
                        value,
                        str
                    )
                    for value in result.values()
                ):

                    return True

        return False

    # --------------------------------------------------
    # README ANALYZER
    # --------------------------------------------------

    def analyze_readmes(
        self,
        previous_results: list
    ) -> Dict[str, str]:

        readmes = {}

        for item in previous_results:

            result = item.get("result")

            if isinstance(result, dict):

                readmes.update(result)

        if not readmes:

            return {
                "error": "No README content available."
            }

        analyses = {}

        for repo_name, readme in readmes.items():

            if not isinstance(
                readme,
                str
            ):
                continue

            if readme.startswith(
                "README fetch failed"
            ):

                analyses[repo_name] = readme
                continue

            analyses[repo_name] = (
                self.analyze_single_readme(
                    repo_name,
                    readme[:3500]
                )
            )

        return analyses

    # --------------------------------------------------
    # SINGLE README ANALYSIS
    # --------------------------------------------------

    def analyze_single_readme(
        self,
        repo_name: str,
        readme: str
    ) -> str:

        prompt = f"""
Analyze this GitHub README.

Repository:
{repo_name}

README:
{readme}

Give a concise analysis containing:

- Purpose
- Technologies
- Key features
- Important implementation details

Rules:
- Use only information present in the README.
- Do not invent facts.
- Keep it under 150 words.
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AURA's GitHub README "
                        "analysis engine."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=250
        )

        content = (
            response.choices[0]
            .message.content
        )

        if not content:

            return (
                "README analysis returned "
                "an empty response."
            )

        return content.strip()

    # --------------------------------------------------
    # LLM
    # --------------------------------------------------

    def run_llm(
        self,
        task: str,
        previous_results: list,
        structured: bool = False
    ):

        # --------------------------------------------------
        # DETERMINISTIC REPOSITORY FILTER
        # --------------------------------------------------

        if structured:

            repositories = []

            ml_keywords = [
                "machine learning",
                "deep learning",
                "neural network",
                "cnn",
                "rnn",
                "lstm",
                "tensorflow",
                "keras",
                "pytorch",
                "scikit-learn",
                "sklearn",
                "classification",
                "regression",
                "prediction",
                "computer vision",
                "object detection",
                "image classification",
                "image colorization",
                "logistic regression",
                "transfer learning",
                "mobilenet",
                "densenet",
                "vgg16",
                "x-ray"
            ]

            for item in previous_results:

                result = item.get("result")

                if not isinstance(
                    result,
                    str
                ):
                    continue

                for line in result.splitlines():

                    line = line.strip()

                    if not line.startswith("- "):
                        continue

                    line = line[2:]

                    parts = [
                        part.strip()
                        for part in line.split("|")
                    ]

                    if not parts:
                        continue

                    repo_name = parts[0]

                    searchable_text = (
                        " ".join(parts).lower()
                    )

                    is_ml_project = any(
                        keyword in searchable_text
                        for keyword in ml_keywords
                    )

                    if (
                        is_ml_project
                        and repo_name
                        not in repositories
                    ):

                        repositories.append(
                            repo_name
                        )

            return json.dumps(
                {
                    "repositories": repositories
                },
                ensure_ascii=False
            )

        # --------------------------------------------------
        # NORMAL LLM REASONING
        # --------------------------------------------------

        previous_text = json.dumps(
            previous_results,
            ensure_ascii=False
        )

        prompt = f"""
Task:
{task}

Previous results:
{previous_text}

Use only the provided information.

Rules:
- Do not invent facts.
- Do not invent repository names.
- Give a concise answer.
"""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AURA's reasoning engine."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=400
        )

        content = (
            response.choices[0]
            .message.content
        )

        if not content:

            raise RuntimeError(
                "LLM returned an empty response."
            )

        return content.strip()