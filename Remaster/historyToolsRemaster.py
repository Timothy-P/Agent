import json
import subprocess
from typing import Any

import ollama


async def compact_history(history_messages: list[dict[str, Any]], memory_summary: str | None, agent_name: str) -> str:
    """Summarize older history while preserving a rolling memory summary."""
    subprocess.run(["ollama", "stop", agent_name], check=False)

    payload = {
        "memory_summary": memory_summary or "",
        "history": history_messages,
    }
    messages = [
        {
            "role": "user",
            "content": json.dumps(payload, indent=2),
        },
    ]

    response = ollama.chat(model="summary", messages=messages, stream=False)
    subprocess.run(["ollama", "stop", "summary"], check=False)

    content = response["message"]["content"]
    return content if isinstance(content, str) else ""
