from typing import Callable, Dict, Any


class Executor:
    """
    Executes plans created by the AURA planner.
    """

    def __init__(self, tools: Dict[str, Callable] | None = None):
        self.tools = tools or {}

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = plan.get("tool")
        goal = plan.get("goal")

        if not tool_name:
            return {
                "success": False,
                "error": "No tool was selected by the planner."
            }

        if tool_name == "llm":
            return {
                "success": True,
                "tool": "llm",
                "result": None,
                "message": "This request can be handled directly by the language model."
            }

        tool = self.tools.get(tool_name)

        if tool is None:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Tool '{tool_name}' is not registered."
            }

        try:
            result = tool(goal)

            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }

        except Exception as exc:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(exc)
            }

    def available_tools(self):
        """
        Return the list of currently registered tools.
        """
        return list(self.tools.keys())