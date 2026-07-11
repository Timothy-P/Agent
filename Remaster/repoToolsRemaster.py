# Remastered tools based on definitions
import os
from pathlib import Path

def read_file(path:str, line_start:int|None=None, line_end:int|None=None):
    """Read file with optional line range."""
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        with open(path) as file:
            if not file.readable():
                return 'error: file unreadable'
            if isinstance(line_start,int) and isinstance(line_end,int):
                lines=[]
                for i,ln in enumerate(file,1):
                    if line_start<=i<=line_end:
                        lines.append(ln)
                return ''.join(lines)
            return file.read()
    except FileNotFoundError:
        return 'error: file does not exist'

def create_file(path:str, contents:str):
    """Create or append a file with given contents."""
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    # open in write mode to overwrite
    try:
        with open(path,'w') as f:
            f.write(contents)
        return f'{path} created'
    except Exception as e:
        return f'error: {e}'

def read_dir(path:str=''):
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        if path=='':
            return os.listdir()
        return os.listdir(path)
    except FileNotFoundError as e:
        return f'error: {e}'

def create_dir(path:str):
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        Path(path).mkdir(parents=True, exist_ok=False)
        return f'{path} created'
    except FileExistsError:
        return f'{path} already exists'
    except PermissionError as e:
        return f'error: {e}'

def write_file(path:str, contents:str):
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        with open(path,'w') as file:
            if file.writable():
                file.write(contents)
                return {'status':'success','msg':f'{path} written','updated_contents':contents}
            return 'error: file unwritable'
    except FileNotFoundError:
        return 'error: file does not exist'

def delete_file(path:str):
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        os.remove(path)
        return f'{path} removed'
    except FileNotFoundError:
        return 'error: file does not exist'

def delete_directory(path:str):
    if '..' in path:
        return 'error: not allowed to access files outside of workspace'
    try:
        os.rmdir(path)
        return f'{path} removed'
    except Exception as e:
        return f'error: {e}'

def search_files(path:str, query:str, max_results:int=10):
    results=set()
    qlower=query.lower()
    for root, dirs, files in os.walk(path,followlinks=False):
        for d in dirs:
            if qlower in d.lower():
                results.add(os.path.join(root,d))
        for f in files:
            if qlower in f.lower():
                results.add(os.path.join(root,f))
        if len(results)>=max_results:
            break
    return list(results)[:max_results]

def tree(path:str, depth:int=3):
    root=Path(path).resolve()
    out=[str(root)]
    def walk(cur:Path,prefix=' ',level=0):
        if level>=depth:return
        try:
            items=sorted(cur.iterdir(), key=lambda x:(x.is_file(),x.name.lower()))
        except PermissionError:
            out.append(prefix+'[permission denied]')
            return
        for i,item in enumerate(items):
            last=i==len(items)-1
            branch='\u2514\u2500\u2500 ' if last else '\u251c\u2500\u2500 '
            out.append(prefix+branch+item.name)
            if item.is_dir():
                new_prefix=prefix+("    " if last else "\u2502   ")
                walk(item,new_prefix,level+1)
    walk(root)
    return '\n'.join(out)

def get_file_info(path:str):
    file=Path(path)
    try:
        stat=file.stat()
        return {'name':file.name,'extension':file.suffix,'size_bytes':stat.st_size,'modified':stat.st_mtime}
    except FileNotFoundError:
        return {'error':'file not found'}
    except PermissionError:
        return {'error':'permission denied'}

def find_text(query:str, path:str='.'):  # default current dir
    results=[]
    root=Path(path).resolve()
    qlower=query.lower()
    for file in root.rglob('*'):
        if not file.is_file():continue
        try:
            text=file.read_text(errors='ignore')
            for ln_num,line in enumerate(text.splitlines(),1):
                if qlower in line.lower():
                    results.append({'file':str(file),'line':ln_num,'content':line.strip()})
        except PermissionError:
            continue
    return results
