"""
GreenMind Assistant.

Two real modes, never a faked one:
1. "llm"  — if AI_API_KEY is configured, calls the Anthropic API with the
   recent conversation history as context, and a system prompt that keeps
   the assistant honest about uncertainty and points to image-based
   diagnosis / professional help for serious cases.
2. "rule_based_fallback" — a small keyword-matched agricultural FAQ
   responder, used when no AI_API_KEY is set. The UI must label this mode
   clearly (mode field in the response) rather than pretending it's the
   full assistant.
"""
import logging
from typing import List, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger("greenmind.chatbot")

SYSTEM_PROMPT = (
    "You are GreenMind Assistant, an agricultural helper for farmers. Answer "
    "questions about crop diseases, symptoms, crop care, fertilizer basics, "
    "pest management, weather-related crop precautions, and disease prevention. "
    "Ask clarifying follow-up questions when symptoms are ambiguous. Never claim "
    "certainty about a diagnosis from a text description alone — recommend "
    "uploading a leaf photo for AI image-based diagnosis when appropriate, and "
    "recommend consulting a local agricultural expert for severe or uncertain cases. "
    "Keep answers concise and practical."
)

_FALLBACK_KB = [
    (["yellow", "yellowing", "leaves"], "Yellowing leaves can indicate nutrient deficiency (often nitrogen), overwatering, or early-stage disease. Can you also check for spots, patchy discoloration, or wilting? A leaf photo uploaded to GreenMind's disease detector will give a much more reliable answer."),
    (["spot", "spots", "patch", "patches"], "Leaf spots are often fungal (like early or late blight) or bacterial. Note the spot color, shape (rings vs. irregular), and which leaves are affected (older/lower vs. new growth) — then upload a photo for image-based diagnosis."),
    (["fertilizer", "npk", "nutrient"], "General guidance: match fertilizer to your crop's growth stage — more nitrogen early for vegetative growth, more phosphorus/potassium during flowering and fruiting. A soil test gives the most reliable recommendation for your specific field."),
    (["pest", "insect", "bug"], "For pest issues, identifying the specific pest matters a lot before choosing treatment. Look for chewed leaves (caterpillars/beetles), sticky residue (aphids/whiteflies), or webbing (mites). A local agricultural extension office can help confirm the pest."),
    (["weather", "rain", "humid"], "Wet, humid conditions favor fungal diseases like blight. If heavy rain is forecast, consider preventive fungicide application (where locally approved) and ensure good field drainage."),
    (["water", "watering", "irrigation"], "Water at the base of the plant rather than overhead when possible — wet foliage for extended periods encourages fungal disease. Early morning watering lets leaves dry faster than evening watering."),
]

_FALLBACK_DEFAULT = (
    "I can help with crop disease symptoms, fertilizer basics, pest management, "
    "and weather-related crop care. Could you tell me more — which crop, and "
    "what you're seeing on the plant? For a reliable diagnosis, uploading a leaf "
    "photo to GreenMind's disease detector is the most accurate option."
)


def _rule_based_reply(message: str) -> str:
    lowered = message.lower()
    for keywords, reply in _FALLBACK_KB:
        if any(kw in lowered for kw in keywords):
            return reply
    return _FALLBACK_DEFAULT


async def get_reply(message: str, history: List[Tuple[str, str]]) -> Tuple[str, str]:
    """
    history: list of (role, content) tuples, oldest first, for context.
    Returns (reply_text, mode) where mode is "llm" or "rule_based_fallback".
    """
    if not settings.AI_API_KEY:
        return _rule_based_reply(message), "rule_based_fallback"

    try:
        messages = [{"role": role, "content": content} for role, content in history]
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.AI_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 500,
                    "system": SYSTEM_PROMPT,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
            return (text or _rule_based_reply(message)), "llm"
    except Exception:
        logger.exception("LLM chatbot call failed — falling back to rule-based reply")
        return _rule_based_reply(message), "rule_based_fallback"
