"""
Base types for GreenMind's agent tools.

Every tool is independently testable: given a ToolContext (a db session
and the authenticated user — nothing else), a tool's run() method can be
called directly in a unit test without going through the LLM or the HTTP
layer at all.

Ownership/authentication rule: ToolContext.current_user is the ONLY
source of "whose data" a tool operates on. Tool parameter schemas (what
the LLM is allowed to pass in) never include a user_id or similar field,
so the LLM cannot ask a tool to act on another user's data even if a
malicious or confused prompt tried to induce that — there is structurally
no parameter for it to fill in.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User


@dataclass
class ToolContext:
    db: Session
    current_user: User


@dataclass
class ToolResult:
    """
    ok=False must always come with a human-readable `error` and no
    fabricated `data` — callers (the agent loop) pass `error` back to the
    LLM as the tool result so it can tell the farmer honestly that the
    lookup failed, rather than inventing an answer.
    """
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @staticmethod
    def success(data: Dict[str, Any]) -> "ToolResult":
        return ToolResult(ok=True, data=data)

    @staticmethod
    def failure(error: str) -> "ToolResult":
        return ToolResult(ok=False, error=error)


class Tool:
    """Base class every GreenMind agent tool implements."""

    name: str = ""
    description: str = ""
    # JSON Schema for the tool's input, in the shape Anthropic's tool-use
    # API expects (a subset of JSON Schema: {"type": "object", "properties": {...}, "required": [...]})
    parameters: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})

    async def run(self, ctx: ToolContext, **kwargs) -> ToolResult:
        raise NotImplementedError

    def schema(self) -> Dict[str, Any]:
        """Anthropic tool-use schema block for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
