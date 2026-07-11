"""
Converts old history JSON files to the new structure.

Only function: `convert`

Takes old history. If it receives new history, returns same value
"""
if __name__ == "__main__":
    print("This file is not made to be run.\nThis is designed to convert old history JSON files.")


def convert(contents:dict[str,list[dict[str,str]]]) -> dict[str,list[dict[str,str]]]:
    # Checking if history is of new or old type
    contentValues = list(contents.values())
    if len(contentValues[0]) > 1:
        return contents

    contents.keys()
    returnVal = {}
    for i in contents.keys():
        returnVal[i] = {"history":[]}
        for f in contents[i]:
            # Appends history 
            returnVal[i]["history"].append(f)
        # Sets name to chat
        # Name can be changed later; temporary
        returnVal[i]["name"] = i
    return returnVal
import json