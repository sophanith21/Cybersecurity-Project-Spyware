import subprocess, os, sys, time, re
# check and delete
def run_as_admin():
    import ctypes
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except: 
        pass

def is_admin():
    import ctypes
    try: 
        return ctypes.windll.shell32.IsUserAnAdmin()
    except: 
        return False

def get_tasks():
    """Get task names only"""
    tasks = []
    try:
        out = subprocess.run(['schtasks', '/query', '/fo', 'CSV'],
                           capture_output=True, text=True, shell=True).stdout
        lines = out.strip().split('\n')
        
        for line in lines[1:]:  # Skip header
            if line:
                parts = line.split('","')
                if len(parts) >= 1:
                    task_name = parts[0].strip('"')
                    tasks.append(task_name)
    except: 
        pass
    
    return tasks

def get_task_details(task_name):
    """Get the actual command/executable for a specific task"""
    try:
        # Query detailed info for this task
        result = subprocess.run(
            ['schtasks', '/query', '/tn', task_name, '/fo', 'LIST', '/v'],
            capture_output=True, text=True, shell=True
        )
        
        if result.returncode != 0:
            return None
        
        # Look for the executable path
        for line in result.stdout.split('\n'):
            line_lower = line.lower()
            # Look for task to run, run as user, or task location
            if 'task to run:' in line_lower or 'run as user:' in line_lower:
                # Extract the command part (after colon)
                if ':' in line:
                    command = line.split(':', 1)[1].strip()
                    if command:  # Only return if not empty
                        return command
        
        return None
    except:
        return None

def delete_task(name):
    try:
        subprocess.run(['schtasks', '/delete', '/tn', name, '/f'], 
                      capture_output=True, shell=True)
        return True
    except: 
        return False

def extract_exe_path(command):
    """Find .exe file path in command - SIMPLER VERSION"""
    if not command:
        return None
    
    # Look for .exe directly
    match = re.search(r'([a-zA-Z]:[\\/][^"\']*\.exe)', command, re.IGNORECASE)
    if match:
        path = match.group(1)
        if os.path.exists(path):
            return path
    
    return None

def delete_file(path):
    """Delete a file"""
    if not path:
        return False
    
    # Try to delete even if path might not exist
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"    ✓ File deleted: {path}")
            return True
        else:
            print(f"    [File not found: {path}]")
            return False
    except Exception as e:
        print(f"    [Could not delete {path}: {e}]")
        return False

def main():
    if not is_admin(): 
        run_as_admin()
        return
    
    print("Running task cleaner... (Ctrl+C to stop)\n")
    
    while True:
        tasks = get_tasks()
        print(f"[{time.strftime('%H:%M:%S')}] Found {len(tasks)} tasks")
        
        for task_name in tasks:
            # Check if task name is suspicious
            sus_words = ['temp', 'tmp', 'update_task', 'system_task', 
                        'maintenance', 'cleaner', 'optimizer', 'helper']
            name_lower = task_name.lower()
            
            if any(word in name_lower for word in sus_words):
                print(f"\n[!] Suspicious task: {task_name}")
                
                # Get the actual command this task runs
                command = get_task_details(task_name)
                
                if command:
                    print(f"    Command: {command[:100]}")
                    
                    # Delete the task
                    if delete_task(task_name):
                        print(f"    ✓ Task deleted")
                        
                        # Try to extract and delete the .exe
                        exe_path = extract_exe_path(command)
                        if exe_path:
                            delete_file(exe_path)
                        else:
                            print(f"    [No .exe path found in command]")
                    else:
                        print(f"    ✗ Failed to delete task")
                else:
                    print(f"    [Could not get task details]")
                    # Delete anyway if suspicious
                    if delete_task(task_name):
                        print(f"    ✓ Task deleted (no details)")
        
        print(f"\n[{time.strftime('%H:%M:%S')}] Scan complete. Next in 10 sec...")
        time.sleep(10)

if __name__ == "__main__":
    main()