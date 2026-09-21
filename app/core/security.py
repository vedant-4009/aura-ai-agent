from enum import Enum
from typing import Dict


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DESTRUCTIVE = "destructive"


class SecurityManager:
    """
    Security layer for AURA tool execution.

    Controls which permission level is required by each tool.
    """

    def __init__(self):
        self.tool_permissions: Dict[str, PermissionLevel] = {
            "github": PermissionLevel.READ,
            "web": PermissionLevel.READ,
            "files": PermissionLevel.READ,
        }

    def get_permission(self, tool_name: str) -> PermissionLevel:
        """
        Return the permission level required by a tool.
        """

        return self.tool_permissions.get(
            tool_name,
            PermissionLevel.DESTRUCTIVE
        )

    def is_allowed(self, tool_name: str) -> bool:
        """
        Check whether a tool is currently allowed to run.
        """

        permission = self.get_permission(tool_name)

        return permission == PermissionLevel.READ

    def check(self, tool_name: str) -> Dict:
        """
        Return a structured security decision.
        """

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