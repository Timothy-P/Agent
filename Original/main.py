from interact import History
from asyncio import run
from json import dumps
from webTools import *
from repoTools import *
from historyTools import compact
import ollama

hist = History()
agent = "agent"

async def compactHist(agentName, **kwargs):
    return await compact(dumps(hist.getHistory(0)["history"]), agentName)

tools = [
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.open_file',
            "description": "Reads a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "line_start": {
                        "type": "number"
                    },
                    "line_end": {
                        "type": "number"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "repo_browser.create_file",
            "description": "Creates a file with initial contents",
            "parameters": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to be created"
                },
                "contents": {
                    "type": "string",
                    "description": "The initial contents to be put in the file"
                }
            },
            "required": ["path","contents"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.readdir',
            "description": "Reads the current working directory's contents. No arguments should be used."
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.mkdir',
            "description": "Creates a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.write_file',
            "description": "Write to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "contents": {
                        "type": "string"
                    },
                },
                "required": ["path", "contents"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.delete_file',
            "description": "Deletes a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.delete_directory',
            "description": "Deletes an empty directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.search',
            "description": "Searches for a string in directory/file names",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "query": {
                        "type": "string"
                    },
                    "max_results": {
                        "type": "number"
                    }
                },
                "required": ["path", "query", "max_results"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'web_browser.search',
            "description": "Searches for a web page based on the query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "max_results": {
                        "type": "number"
                    }
                },
                "required": ["query", "max_results"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'web_browser.open',
            "description": "Opens the requested web page",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.tree',
            "description": "Lists the current directory based on the depth like `tree`",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "depth": {
                        "type": "number"
                    }
                },
                "required": ["path", "depth"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.get_file_info',
            "description": "Retrieves the file's basic info",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'repo_browser.find_text',
            "description": "Finds text within files recursively",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'history_edit.context_compact',
            "description": "Compacts the current history to increase functionality",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    },
]

# It's horrid, I know, but it's just translating 
# the tool name into the real functions
available_tools = {'repo_browser.open_file':read_file, "repo_browser.create_file":create_file, 'repo_browser.readdir':read_dir, 'repo_browser.mkdir':create_dir, 'repo_browser.write_file': write_file, 'repo_browser.delete_file': delete_file, 'repo_browser.delete_directory': delete_directory, 'repo_browser.search':search_files,'repo_browser.tree':tree,'repo_browser.get_file_info':get_file_info,'repo_browser.find_text':find_text, 'web_browser.search':web_search, 'web_browser.open':open_url, 'history_edit.context_compact':compactHist(agent)}

autoApprove = False
neverAsk = False
def userConf(toolName:str, args:dict, thoughts:str):
    global neverAsk, autoApprove
    if autoApprove:
        return True
    print("\n\nThe agent has requested to use a tool")
    print(f"Model's thoughts: {thoughts}")
    print(f"Tool name: {toolName}")
    print("Arguments:")
    for i in args:
        print(f"    {i}: {args[i]}")
    while True:
        print("\nWould you like to approve this tool usage?")
        print("[Y] Yes, [N] No, [E] Explain")
        prompt = input(">>>")

        if "y" in prompt.lower():
            if not neverAsk:
                print("\nWould you like all tool calls to be auto-approved from now on?")
                print("[Y] Yes, [N] No, [D] Don't ask again")
                askAgain = input(">>>")
                if "y" in askAgain.lower():
                    autoApprove = True
                elif "n" in askAgain.lower():
                    return True
                elif "d" in askAgain.lower():
                    neverAsk = True
            return True
        elif "n" in prompt.lower():
            return False
        elif "e" in prompt.lower():
            if toolName == "repo_browser.open_file":
                print("\n The agent will only read the indicated file.")
            elif toolName == "repo_browser.create_file":
                print("\n The agent will create a new file. If it already exists, contents will be appended.")
            elif toolName == "repo_browser.readdir":
                print("\nThe agent will read the current working directory. It'll receive the file/folder names, but nothing else.")
            elif toolName == "repo_browser.mkdir":
                print("\nThe agent will create a new, empty directory.")
            elif toolName == "repo_browser.write_file":
                print("\nThe agent will overwrite a file, causing the previous contents to be lost. Making a copy is recommended.")
            elif toolName == "repo_browser.delete_file":
                print("\nThe agent will delete a file, causing the file and its contents to be lost. Making a backup is recommended.")
            elif toolName == "repo_browser.readdir":
                print("\nThe agent will read the current working directory. It'll receive the file/folder names, but nothing else.")
            elif toolName == "repo_browser.delete_directory":
                print("\nThe agent will delete an empty directory. If not empty, the operation fill fail.")
            elif toolName == "repo_browser.search":
                print("\nThe agent will search folder and file names for the specified string.")
            elif toolName == "web_browser.search":
                print("\nThe agent will use DuckDuckGo to make a search. No page will be visited or opened.")
            elif toolName == "web_browser.open":
                print("\nThe agent will open the page at the URL and retrieve the contents.")
            else:
                print("\nUnknown tool. The call will likely fail.")
        else:
            print("\nUnrecognized input. Try again.")

retry = True
toolLoop:int = 0
async def sendPrompt(model:str, prompt:str, toolCall:bool = False):
    global toolLoop, retry

    if not toolCall:
        hist.add([{"role":"user","content":prompt}],0)
        try:
            data = ollama.chat(model=model, messages=hist.getHistory(0)["history"], stream=False) # type: ignore
        except ollama.ResponseError:
            print("ResponseError has occured.")
            if retry:
                hist.add([{"role":"tool","content":"ResponseError has occured. Retry has been attempted. "}],0)
                retry = False
                await sendPrompt(model, prompt, toolCall)
            else:
                print("Second ResponseError in a row. Quitting...")
                quit()
        else:
            response: ollama.ChatResponse = data
    else:
        try:
            data = ollama.chat(model=model, messages=hist.getHistory(0)["history"], stream=False) # type: ignore
        except ollama.ResponseError:
            print("ResponseError has occured.")
            if retry:
                hist.add([{"role":"tool","content":"ResponseError has occured. Retry has been attempted. "}],0)
                retry = False
                await sendPrompt(model, prompt, toolCall)
            else:
                print("Second ResponseError in a row. Exiting...")
                exit()
        else:
            response: ollama.ChatResponse = data

    retry = True

    #thinking = response["message"]["thinking"]
    content = response["message"]["content"] # type: ignore
    if response.message.tool_calls: # type: ignore
        for call in response.message.tool_calls: # type: ignore
            toolName: str = call.function.name # type: ignore
            args: dict = call.function.arguments # type: ignore

            if toolLoop == 30:
                hist.add([{"role":"tool","content":"Tool loop break activated; 30 consecutive tool calls was made."}],0)
                print("\n\n30 tool consecutive tool calls was made. Tool loop break was activated.\n")
                break

            if toolName.split("<|")[0] == 'assistant':
                try:
                    toolName = args["tool"]
                    args = args["args"]
                except KeyError:
                    continue
            tool = {"tool":toolName, "args":args}

            if not userConf(toolName, args, response.message.thinking): # type: ignore
                hist.add([{"role":"assistant","content":f"{tool}"},{"role":"tool","content":"User objection. Tool call was refused."}],0)
                await sendPrompt(model, prompt, True)

            
            try:
                result:str = available_tools[toolName](**args)
            except KeyError:
                print("Agent attempted to call invalid tool")
                hist.add([{"role":"assistant","content":f"{tool}"},{"role":"tool","content":f"Invalid tool: f{toolName}"}],0)
                await sendPrompt(model, prompt, True)
                quit()
            toolLoop += 1




            returnString:dict = {"tool":toolName, "content":result}# type: ignore
            hist.add([{"role":"assistant","content":f"{tool}"},{"role":"tool", "content":dumps(returnString)}],0)
            await sendPrompt(model, prompt, True)
    else:
        toolLoop = 0
        print(content)

if __name__ == "__main__":
    while True:
        run(sendPrompt(agent,input(">")))