from enum import Enum
from typing import Dict


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DESTRUCTIVE = "destructive"


class SecurityManager:

    def __init__(self):

        self.tool_permissions = {
            "github": PermissionLevel.READ,
            "github_readme": PermissionLevel.READ,
            "web": PermissionLevel.READ,
            "files": PermissionLevel.READ,
            "llm": PermissionLevel.READ,
        }

    def get_permission(self, tool_name: str) -> PermissionLevel:

        return self.tool_permissions.get(
            tool_name,
            PermissionLevel.DESTRUCTIVE
        )

    def is_allowed(self, tool_name: str) -> bool:

        return self.get_permission(
            tool_name
        ) == PermissionLevel.READ

    def check(self, tool_name: str) -> Dict:

        permission = self.get_permission(tool_name)

        if permission == PermissionLevel.READ:

            return {
                "allowed": True,
                "tool": tool_name,
                "permission": permission.value,
                "reason": "Read-only operation is allowed."
            }

        return {
            "allowed": False,
            "tool": tool_name,
            "permission": permission.value,
            "reason": (
                f"Tool '{tool_name}' requires "
                f"{permission.value} permission."
            )
        }