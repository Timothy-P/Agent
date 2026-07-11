import subprocess, os
from pathlib import Path

def read_file(path:str, line_start:int|None = None, line_end:int|None = None, **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    try:
        with open(path) as file:
            if file.readable():
                returnString:str = ""
                if type(line_start) == int and type(line_end) == int:
                    for i in range(line_start,line_end+1):
                        if i < line_end and i > line_start:
                            returnString += file.readline()
                else:
                    returnString += file.read()
                return returnString
            return "error: file unreadable"
    except FileNotFoundError:
        return "error: file doesn't exist"
    
def create_file(path:str, contents:str, **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    with open(path, mode="a") as file:
        file.write(contents)
        return path+" created"

def read_dir(path:str = "", **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    if path == "":
        result = os.listdir()
    else:
        result = os.listdir(path)
    return result

def create_dir(path: str, **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    results = subprocess.run(["mkdir", path], capture_output=True, text=True)
    if results.stderr:
        return "error: "+results.stderr
    return path+" created"

def write_file(path:str, contents:str, **kwargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    try:
        with open(path, "w") as file:
            if file.writable():
                file.write(contents)
                return {
                    "status": "success",
                    "msg": f"{path} written",
                    "updated_contents": contents
                }
                
            return "error: file unwritable"
    except FileNotFoundError:
        return "error: file doesn't exist"

def delete_file(path:str, **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    results = subprocess.run(["rm", path], capture_output=True, text=True)
    if results.stderr:
        return "error: "+results.stderr
    return path+" removed"

def delete_directory(path:str, **kargs):
    if ".." in path:
        return "error: not allowed to access files outside of workspace"
    results = subprocess.run(["rmdir", path], capture_output=True, text=True)
    if results.stderr:
        return "error: "+results.stderr
    return path+" removed"

def search_files(path: str, query: str, max_results: int = 10, **kwargs):
    """
    Recursively searches files and directories under path.
    Returns matching paths without duplicates.
    """

    results = set()
    query_lower = query.lower()

    try:
        for root, dirs, files in os.walk(path, followlinks=False):
            for directory in dirs:
                if query_lower in directory.lower():
                    results.add(os.path.join(root, directory))

            for file in files:
                if query_lower in file.lower():
                    results.add(os.path.join(root, file))

            if len(results) >= max_results:
                break

    except PermissionError:
        pass

    return list(results)[:max_results]

def tree(path: str, depth: int = 3):
    """
    Returns a readable directory tree.
    """

    root = Path(path).resolve()
    output = [str(root)]

    def walk(current: Path, prefix: str = "", level: int = 0):
        if level >= depth:
            return

        try:
            items = sorted(
                current.iterdir(),
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except PermissionError:
            output.append(prefix + "[permission denied]")
            return

        for index, item in enumerate(items):
            is_last = index == len(items) - 1

            branch = "└── " if is_last else "├── "
            output.append(prefix + branch + item.name)

            if item.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                walk(item, new_prefix, level + 1)

    walk(root)

    return "\n".join(output)

def get_file_info(path: str):
    """
    Returns basic information about a file.
    """

    file = Path(path)

    try:
        stat = file.stat()

        return {
            "name": file.name,
            "extension": file.suffix,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime
        }

    except FileNotFoundError:
        return {
            "error": "file not found"
        }

    except PermissionError:
        return {
            "error": "permission denied"
        }

def find_text(query: str, path: str = "."):
    """
    Finds text inside files recursively.
    """

    results = []

    root = Path(path).resolve()
    query = query.lower()

    for file in root.rglob("*"):
        if not file.is_file():
            continue

        try:
            text = file.read_text(errors="ignore")

            for line_number, line in enumerate(
                text.splitlines(),
                start=1
            ):
                if query in line.lower():
                    results.append(
                        {
                            "file": str(file),
                            "line": line_number,
                            "content": line.strip()
                        }
                    )

        except PermissionError:
            continue

    return results
