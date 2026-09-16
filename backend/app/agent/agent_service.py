"""
GreenMind AI Agent.

Two real modes, same contract as the pre-agent chatbot_service:
1. "llm" — AI_API_KEY is configured. Calls the Anthropic Messages API with
   GreenMind's tool schemas attached. If the model requests a tool, the
   tool is executed against the CURRENT AUTHENTICATED USER ONLY (see
   ToolContext) and the result is fed back to the model, looping until it
   produces a final text reply (capped at MAX_TOOL_ROUNDS to bound cost
   and latency, and to guarantee the loop terminates).
2. "rule_based_fallback" — no AI_API_KEY configured, or the LLM call
   fails for any reason. Reuses chatbot_service's existing, unmodified
   rule-based FAQ responder — same function, same trigger condition, same
   fallback text, as before this phase existed. This mode never calls
   tools; it's a pure text responder, exactly as it always was.

Safety invariants enforced here, not just documented:
- Tool input schemas (see app/agent/registry.py) never include a user_id
  field, and ToolContext is built once per request from the authenticated
  user resolved by FastAPI's get_current_user dependency — a tool can
  only ever act on the current user's own data.
- A tool_result is only ever built from a ToolResult the tool itself
  returned; the agent loop never fabricates a tool result on the model's
  behalf, and never invents a reply attributing information to a tool
  that wasn't actually called successfully.
- An unknown tool name requested by the model is answered with an error
  tool_result (not a crash, not a fabricated result) so the model can
  recover within the conversation.
"""
import json
import logging
from typing import List, Tuple

import httpx

from app.agent.registry import all_tool_schemas, get_tool
from app.agent.tools.base import ToolContext
from app.core.config import settings
from app.services.chatbot_service import _rule_based_reply

logger = logging.getLogger("greenmind.agent")

MAX_TOOL_ROUNDS = 4
ANTHROPIC_MODEL = "claude-sonnet-4-6"

_LOCALE_NAMES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
}

_BASE_SYSTEM_PROMPT = (
    "You are GreenMind Assistant, an agricultural helper for farmers. Answer "
    "questions about crop diseases, symptoms, crop care, fertilizer basics, "
    "pest management, weather-related crop precautions, and disease prevention. "
    "You have tools to look up the farmer's real prediction history, real "
    "weather data, real disease/recommendation reference information, and to "
    "generate a PDF report — use them whenever a question depends on facts "
    "you don't already have, rather than guessing. NEVER state a specific "
    "diagnosis, confidence value, weather number, or history item unless it "
    "came from a tool result in this conversation. If a tool fails or returns "
    "no data, say so honestly instead of filling in a plausible-sounding "
    "answer. Never claim certainty about a diagnosis from a text description "
    "alone — recommend uploading a leaf photo for AI image-based diagnosis "
    "when appropriate, and recommend consulting a local agricultural expert "
    "for severe or uncertain cases. Keep answers concise and practical."
)


def _system_prompt(locale: str = None) -> str:
    if locale and locale != "en" and locale in _LOCALE_NAMES:
        return (
            f"{_BASE_SYSTEM_PROMPT} Respond in {_LOCALE_NAMES[locale]}, matching the "
            "farmer's selected language, regardless of what language their message is in."
        )
    return _BASE_SYSTEM_PROMPT


async def _call_anthropic(client: httpx.AsyncClient, messages: list, locale: str) -> dict:
    response = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 800,
            "system": _system_prompt(locale),
            "messages": messages,
            "tools": all_tool_schemas(),
        },
    )
    response.raise_for_status()
    return response.json()


async def _execute_tool(ctx: ToolContext, tool_use_block: dict) -> dict:
    """Runs one tool_use block and returns an Anthropic tool_result content block."""
    tool_name = tool_use_block.get("name")
    tool_input = tool_use_block.get("input") or {}
    tool_use_id = tool_use_block["id"]

    tool = get_tool(tool_name)
    if tool is None:
        logger.warning("Agent requested unknown tool: %s", tool_name)
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": f"Unknown tool '{tool_name}'. It is not available.",
            "is_error": True,
        }

    try:
        result = await tool.run(ctx, **tool_input)
    except Exception:
        logger.exception("Tool '%s' raised an unexpected error", tool_name)
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": f"The '{tool_name}' tool failed unexpectedly.",
            "is_error": True,
        }

    if not result.ok:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result.error or "Tool call failed.",
            "is_error": True,
        }

    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": json.dumps(result.data),
    }


async def get_agent_reply(
    ctx: ToolContext,
    message: str,
    history: List[Tuple[str, str]],
    locale: str = None,
) -> Tuple[str, str, List[str]]:
    """
    Returns (reply_text, mode, tools_used).
    mode is "llm" or "rule_based_fallback" — identical vocabulary to the
    pre-agent chatbot_service, so the frontend's existing mode check
    (Chat.tsx: m.mode === "rule_based_fallback") keeps working unchanged.
    """
    if not settings.AI_API_KEY:
        return _rule_based_reply(message), "rule_based_fallback", []

    tools_used: List[str] = []

    try:
        messages = [{"role": role, "content": content} for role, content in history]
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(MAX_TOOL_ROUNDS):
                data = await _call_anthropic(client, messages, locale)
                content_blocks = data.get("content", [])
                tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]

                if not tool_use_blocks:
                    text = "".join(
                        b.get("text", "") for b in content_blocks if b.get("type") == "text"
                    )
                    return (text or _rule_based_reply(message)), "llm", tools_used

                # Model wants to use one or more tools: execute each against
                # the current authenticated user, then continue the loop.
                messages.append({"role": "assistant", "content": content_blocks})

                tool_result_blocks = []
                for block in tool_use_blocks:
                    tools_used.append(block.get("name"))
                    tool_result_blocks.append(await _execute_tool(ctx, block))

                messages.append({"role": "user", "content": tool_result_blocks})

            # Exceeded MAX_TOOL_ROUNDS without a final text reply — fail
            # safe rather than looping forever or fabricating a reply.
            logger.warning("Agent exceeded max tool rounds without a final reply")
            return _rule_based_reply(message), "rule_based_fallback", tools_used

    except Exception:
        logger.exception("Agent LLM call failed — falling back to rule-based reply")
        return _rule_based_reply(message), "rule_based_fallback", tools_used
