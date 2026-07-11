"""
A simple way of interacting with Ollama.

The many functions are for a pre-made `History` variable, but you can also create your own.

Some other functions are for interacting with Ollama itself, like removing, listing, or creating models.
"""

import ollama, json # type: ignore

# Basic functions

class History:
    """
    History class maintains a dictionary of chat histories.

    Each chat is identified by a key 'chat-{chat_id}' and stores a list of message dicts.

    Way of storing:
        {"chat-0":{
            "history":[
                {"role":"user","content":"Test 1"},
                {"role":"assistant","content":"Test 2"},
                {"role":"user","content":"Test 3"},
                {"role":"assistant","content":"Test 4"},
            ],
            "name":"Foobar"
        }
    """
    def __init__(self, file="chats.json") -> None:
        self.value:dict[str,list[dict[str,str]]] = {}
        self.loadHistory(file)

    def add(self, addition: list[dict[str, str]], chat: int) -> bool:
        """
        Adds to the history.

        Structure for storing: 
            {"chat-0":{
                "history":[
                    {"role":"user","content":"Test 1"},
                    {"role":"assistant","content":"Test 2"},
                    {"role":"user","content":"Test 3"},
                    {"role":"assistant","content":"Test 4"},
                ],
                "name":"Foobar"
            }

        The chat parameter is for what "chat" is being saved to.

        Note: If chat doesn't exist, it will be created.
        """
        # Validate each message in addition
        for i in addition:
            if len(i) != 2:
                return False
            if i["role"] not in ["user", "assistant", "tool", "system"]:
                return False
            if "content" not in i:
                return False
        chat_key = f"chat-{chat}"
        if chat_key not in self.value:
            # If your IDE is complaining, ignore it.
            # It works perfectly fine.
            self.value[chat_key] = {"history":[],"name":chat_key} # type: ignore

            for i in addition:
                self.value[chat_key]["history"].append(i) # type: ignore
        else:
            # If your IDE is complaining, ignore it.
            # It works perfectly fine.
            for i in addition:
                self.value[chat_key]["history"].append(i) # type: ignore
        return True

    def remove(self, remove: int, chat: int) -> bool:
        """
        Removes a message at index 'remove' from the chat history for the given chat.

        Returns True if successful, False otherwise.
        """
        chat_key = f"chat-{chat}"
        if chat_key not in self.value:
            return False
        if remove < 0 or remove >= len(self.value[chat_key]):
            return False
        del self.value[chat_key][remove]
        return True

    def edit(self, item: int, newVal: str, chat: int, role:str) -> bool:
        """
        Edits the 'content' of a message at index 'item' in the chat history for the given chat.

        Optionally checks for role match if provided.

        Returns True if successful, False otherwise.

        """
        chat_key = f"chat-{chat}"
        if chat_key not in self.value:
            return False
        if item < 0 or item >= len(self.value[chat_key]):
            return False
        if role and self.value[chat_key][item]["role"] != role:
            return False
        self.value[chat_key][item]["content"] = newVal
        return True

    def getHistory(self, chat: int) -> dict[str, list[dict[str,str]] | str]:
        """
        Returns the chat history (list of messages) for the given chat.

        Returns an empty list if chat does not exist.
        """
        chat_key = f"chat-{chat}"
        if chat_key in self.value:
            content = self.value[chat_key].copy()
            # If your IDE is complaining, ignore it.
            # It works perfectly fine.
            return {"history": content["history"], "name": content["name"]} # type: ignore
        return {"history": [], "name": ""}
    
    def saveHistory(self, file:str) -> bool:
        """
        Saves the current history to a specific file, given that it is possible.

        If it can't write, False. True otherwise.
        """
        saveFile = open(file, "w")
        if saveFile.writable():
            saveFile.write(json.dumps(self.value))
            return True
        return False
        
    def loadHistory(self, file:str) -> bool:
        """
        Loads history from a given file.

        If file exists and can be loaded, loads file and returns `True`. Otherwise, returns `False`.

        Warning: This will delete current contents
        """
        from historyConvert import convert

        try:
            loadFile = open(file, "r")
        except FileNotFoundError:
            print(f">>> interact.py: {file} doesn't exist")
            return False
        if loadFile.readable():
            contents = loadFile.read()
            if len(contents) > 2:
                # Finally converting to the new. Hopefully it works.
                self.value = convert(json.loads(contents))
                loadFile.close()
                return True
        
        loadFile.close()
        return False
        
    def editChatName(self, newName:str, chatNum:int) -> bool:
        """
        Edits the name to the chat specified.

        If the chat name is modified, returns True.

        False otherwise.
        """

        self.value["chat-"+str(chatNum)][0] = newName # type: ignore

        return False







# Pre-made for those who don't want to define the history variable themselves.
__hist = History()
async def sendPrompt(model:str, prompt:str, chat:int) -> str:
    """
    Sends the prompt to a model.

    Autosaves to chat.
    """
    if (type(model) == None or type(prompt) == None):
        return ""
    # If your IDE is complaining, ignore it.
    # It works perfectly fine.
    currentHist = __hist.getHistory(chat)["history"].copy() # type: ignore
    currentHist.append({"role":"user","content":prompt})
    response: ollama.ChatResponse = ollama.chat(model=model, messages=currentHist, stream=False)
    content = response["message"]["content"]
    if type(content) == str:
        __hist.add([{"role":"user","content":prompt},{"role":"assistant","content":content}],chat)
        __hist.saveHistory("chats.json")
        return content
    return ""

def removeHistory(item:int, chat:int) -> bool:
    """
    Removes a piece of history, provided that the item exists.
    """
    return __hist.remove(item, chat)
    
def editHistory(item:int, newValue:str, chat:int, role:str) -> bool:
    """
    Edits a piece of history, provided that it exists.

    If it succeeds, then it'll return True. False otherwise.
    """
    return __hist.edit(item,newValue,chat,role)
    
def getHistory(chat:int) -> dict[str,list[dict[str,str]] | str]:
    """
    Returns the history of a given chat. If the chat doesn't exist, returns empty list.
    """
    return __hist.getHistory(chat)

def saveHistory(file:str) -> bool:
    return __hist.saveHistory(file)

def loadHistory(file:str) -> Exception|bool:
    return __hist.loadHistory(file)