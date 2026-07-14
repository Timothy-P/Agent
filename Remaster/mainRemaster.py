import asyncio
import inspect
import json
from typing import Any

import ollama

from historyToolsRemaster import compact_history
from interact import History
from repoToolsRemaster import (
    create_dir,
    create_file,
    delete_directory,
    delete_file,
    find_text,
    get_file_info,
    read_dir,
    read_file,
    search_files,
    tree,
    write_file,
)
from webToolsRemaster import open_url, web_search

hist = History()
agent = "agent"
memory_summary: str | None = None
COMPACTION_THRESHOLD = 24
RECENT_MESSAGES_TO_KEEP = 8


async def compact_messages(history_messages: list[dict[str, Any]], agent_name: str) -> str:
    global memory_summary
    if not history_messages:
        return memory_summary or ""

    older_messages = history_messages[:-RECENT_MESSAGES_TO_KEEP] if len(history_messages) > RECENT_MESSAGES_TO_KEEP else []
    recent_messages = history_messages[-RECENT_MESSAGES_TO_KEEP:] if len(history_messages) > RECENT_MESSAGES_TO_KEEP else history_messages

    if not older_messages:
        return memory_summary or ""

    memory_summary = await compact_history(older_messages, memory_summary, agent_name)
    compacted_history = [
        {"role": "system", "content": f"Conversation memory summary:\n{memory_summary or 'No prior memory.'}"}
    ] + recent_messages
    hist.value["chat-0"]["history"] = compacted_history  # type: ignore[index]
    return memory_summary or ""


async def compact_hist(agent_name: str, **_: Any) -> str:
    history_messages = hist.getHistory(0)["history"]
    return await compact_messages(history_messages, agent_name)


def build_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "repo_browser.open_file",
                "description": "Reads a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "line_start": {"type": "number"},
                        "line_end": {"type": "number"},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.create_file",
                "description": "Creates a file with initial contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "contents": {"type": "string"},
                    },
                    "required": ["path", "contents"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.readdir",
                "description": "Reads the current working directory's contents.",
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.mkdir",
                "description": "Creates a directory",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.write_file",
                "description": "Write to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "contents": {"type": "string"},
                    },
                    "required": ["path", "contents"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.delete_file",
                "description": "Deletes a file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.delete_directory",
                "description": "Deletes an empty directory",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.search",
                "description": "Searches for a string in directory/file names",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "query": {"type": "string"},
                        "max_results": {"type": "number"},
                    },
                    "required": ["path", "query", "max_results"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_browser.search",
                "description": "Searches for a web page based on the query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "number"},
                    },
                    "required": ["query", "max_results"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_browser.open",
                "description": "Opens the requested web page",
                "parameters": {
                    "type": "object",
                    "properties": {"url": {"type": "string"}},
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.tree",
                "description": "Lists the current directory based on the depth like tree",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "depth": {"type": "number"},
                    },
                    "required": ["path", "depth"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.get_file_info",
                "description": "Retrieves the file's basic info",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repo_browser.find_text",
                "description": "Finds text within files recursively",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "history_edit.context_compact",
                "description": "Compacts the current history to increase functionality",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        },
    ]


available_tools = {
    "repo_browser.open_file": read_file,
    "repo_browser.create_file": create_file,
    "repo_browser.readdir": read_dir,
    "repo_browser.mkdir": create_dir,
    "repo_browser.write_file": write_file,
    "repo_browser.delete_file": delete_file,
    "repo_browser.delete_directory": delete_directory,
    "repo_browser.search": search_files,
    "repo_browser.tree": tree,
    "repo_browser.get_file_info": get_file_info,
    "repo_browser.find_text": find_text,
    "web_browser.search": web_search,
    "web_browser.open": open_url,
    "history_edit.context_compact": compact_hist,
}

tools = build_tool_definitions()


class ToolApprovalState:
    def __init__(self) -> None:
        self.auto_approve = False
        self.never_ask = False

    def confirm(self, tool_name: str, args: dict[str, Any], thoughts: str) -> bool:
        if self.auto_approve:
            return True

        print("\n\nThe agent has requested to use a tool")
        print(f"Model's thoughts: {thoughts}")
        print(f"Tool name: {tool_name}")
        print("Arguments:")
        for key, value in args.items():
            print(f"    {key}: {value}")

        while True:
            print("\nWould you like to approve this tool usage?")
            print("[Y] Yes, [N] No, [E] Explain")
            prompt = input(">>>").strip().lower()

            if prompt.startswith("y"):
                if not self.never_ask:
                    print("\nWould you like all tool calls to be auto-approved from now on?")
                    print("[Y] Yes, [N] No, [D] Don't ask again")
                    answer = input(">>>").strip().lower()
                    if answer.startswith("y"):
                        self.auto_approve = True
                    elif answer.startswith("n"):
                        return True
                    elif answer.startswith("d"):
                        self.never_ask = True
                return True

            if prompt.startswith("n"):
                return False

            if prompt.startswith("e"):
                self._explain_tool(tool_name)
                continue

            print("\nUnrecognized input. Try again.")

    def _explain_tool(self, tool_name: str) -> None:
        explanations = {
            "repo_browser.open_file": "The agent will only read the indicated file.",
            "repo_browser.create_file": "The agent will create a new file. If it already exists, contents will be appended.",
            "repo_browser.readdir": "The agent will read the current working directory. It will receive the file/folder names, but nothing else.",
            "repo_browser.mkdir": "The agent will create a new, empty directory.",
            "repo_browser.write_file": "The agent will overwrite a file, causing the previous contents to be lost. Making a copy is recommended.",
            "repo_browser.delete_file": "The agent will delete a file, causing the file and its contents to be lost. Making a backup is recommended.",
            "repo_browser.delete_directory": "The agent will delete an empty directory. If it is not empty, the operation will fail.",
            "repo_browser.search": "The agent will search folder and file names for the specified string.",
            "web_browser.search": "The agent will use DuckDuckGo to make a search. No page will be visited or opened.",
            "web_browser.open": "The agent will open the page at the URL and retrieve the contents.",
        }
        print(f"\n{explanations.get(tool_name, 'Unknown tool. The call will likely fail.')}")


approval_state = ToolApprovalState()
retry = True
tool_loop = 0


async def invoke_tool(tool_name: str, args: dict[str, Any]) -> Any:
    tool = available_tools.get(tool_name)
    if tool is None:
        raise KeyError(tool_name)

    result = tool(**args)
    if inspect.isawaitable(result):
        return await result
    return result


async def send_prompt(model: str, prompt: str, tool_call: bool = False) -> None:
    global retry, tool_loop

    if not tool_call:
        hist.add([{"role": "user", "content": prompt}], 0)

    history_messages = hist.getHistory(0)["history"]
    if len(history_messages) >= COMPACTION_THRESHOLD:
        await compact_messages(history_messages, agent)

    while True:
        try:
            response = ollama.chat(model=model, messages=hist.getHistory(0)["history"], stream=False)  # type: ignore[arg-type]
        except ollama.ResponseError:
            print("ResponseError has occurred.")
            if retry:
                hist.add([{"role": "tool", "content": "ResponseError has occurred. Retry has been attempted."}], 0)
                retry = False
                continue

            print("Second ResponseError in a row. Exiting...")
            raise

        retry = True
        content = response["message"]["content"]  # type: ignore[index]
        tool_calls = getattr(response.message, "tool_calls", None)  # type: ignore[attr-defined]

        if not tool_calls:
            tool_loop = 0
            hist.add([{"role":"assistant","content":content}],0)
            print(content)
            return

        for call in tool_calls:
            tool_name: str = call.function.name  # type: ignore[attr-defined]
            args: dict[str, Any] = dict(call.function.arguments or {})  # type: ignore[attr-defined]

            if tool_loop == 30:
                hist.add([{"role": "tool", "content": "Tool loop break activated; 30 consecutive tool calls were made."}], 0)
                print("\n\n30 consecutive tool calls were made. Tool loop break was activated.\n")
                return

            if tool_name.split("<|")[0] == "assistant":
                try:
                    tool_name = args["tool"]
                    args = dict(args["args"])
                except (KeyError, TypeError, ValueError):
                    continue

            tool_payload = {"tool": tool_name, "args": args}
            if not approval_state.confirm(tool_name, args, getattr(response.message, "thinking", "")):
                hist.add(
                    [
                        {"role": "assistant", "content": json.dumps(tool_payload)},
                        {"role": "tool", "content": "User objection. Tool call was refused."},
                    ],
                    0,
                )
                return

            try:
                result = await invoke_tool(tool_name, args)
            except KeyError:
                print("Agent attempted to call an invalid tool")
                hist.add(
                    [
                        {"role": "assistant", "content": json.dumps(tool_payload)},
                        {"role": "tool", "content": f"Invalid tool: {tool_name}"},
                    ],
                    0,
                )
                return
            except Exception as exc:  # pragma: no cover - defensive guard
                print(f"Tool execution failed: {exc}")
                hist.add(
                    [
                        {"role": "assistant", "content": json.dumps(tool_payload)},
                        {"role": "tool", "content": f"Tool execution failed: {exc}"},
                    ],
                    0,
                )
                return

            tool_loop += 1
            return_payload = {"tool": tool_name, "content": result}
            hist.add(
                [
                    {"role": "assistant", "content": json.dumps(tool_payload)},
                    {"role": "tool", "content": json.dumps(return_payload)},
                ],
                0,
            )

            break


if __name__ == "__main__":
    try:
        while True:
            asyncio.run(send_prompt(agent, input(">")))
    except KeyboardInterrupt:
        print("\nGoodbye.")
