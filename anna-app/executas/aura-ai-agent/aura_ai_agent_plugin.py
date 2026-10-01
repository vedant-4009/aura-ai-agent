"""AURA AI Agent Executa for Anna."""

import json
import sys

from aura_core.orchestrator import Orchestrator


MANIFEST = {
    "name": "tool-dev-aura-ai-agent",
    "version": "0.2.0",
    "tools": [
        {
            "name": "run",
            "description": "Run the AURA AI Agent with a natural-language request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The user's request for AURA.",
                    }
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        }
    ],
}


def invoke(method: str, args: dict) -> dict:
    if method == "run":
        user_input = args.get("input", "").strip()

        if not user_input:
            return {
                "success": False,
                "error": "Input cannot be empty.",
            }

        result = Orchestrator().run(user_input)

        return {
            "success": True,
            "data": {
                "input": result.get("input"),
                "plan": result.get("plan"),
                "execution": result.get("execution"),
                "response": result.get("response"),
            },
        }

    return {
        "success": False,
        "error": f"unknown method: {method}",
    }


def main() -> None:
    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        req = json.loads(line)

        try:
            if req.get("method") == "describe":
                result = MANIFEST

            elif req.get("method") == "health":
                result = {"status": "ready"}

            elif req.get("method") == "invoke":
                result = invoke(
                    req["params"]["tool"],
                    req["params"].get("arguments", {}),
                )

            else:
                raise ValueError(
                    f"unknown rpc: {req.get('method')}"
                )

            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req.get("id"),
                        "result": result,
                    }
                )
                + "\n"
            )

        except Exception as e:
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req.get("id"),
                        "error": {
                            "code": -32601,
                            "message": str(e),
                        },
                    }
                )
                + "\n"
            )

        sys.stdout.flush()


if __name__ == "__main__":
    main()
