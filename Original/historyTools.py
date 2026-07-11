import ollama, subprocess
async def compact(history:str, agentName:str):
    subprocess.run(["ollama", "stop", agentName])

    messages = [{"role":"system","content":f"Summarize the following:\n\n{history}"}]

    response = ollama.chat(model="summary", messages=messages, stream=False)

    subprocess.run(["ollama", "stop", "summary"])

    return response["message"]["content"]
