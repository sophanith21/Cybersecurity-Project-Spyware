import os
import mss
from datetime import datetime
import time
import requests
import psutil
import win32gui
import win32process
serverURL = "http://127.0.0.1:3000/upload"  # Replace <SERVER_IP> with server IP
target_app = "chrome.exe" 

def isAppActive(target_app):
    activeWindow = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(activeWindow)

    try:
        proc = psutil.Process(pid)
        return proc.name().lower() == target_app.lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    


def isAppRunning(target_app):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == target_app:
            print("The chrome is opened")
            return True
    return False

def screenshotLoop():
    with mss.mss() as sct:
        folder = "screenshots"
        os.makedirs(folder, exist_ok=True)
        try:
            # while True: 

                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(folder, f"screenshot_{timestamp}.png")	
                sct.shot(output=filename)
                print(f"Saved {filename}")
                try: 
                    with open(filename, "rb") as f:
                        files = {"image": f}
                        response = requests.post(serverURL, files=files)
                        print("server response:", response.text)
                except Exception as e: 
                    print("Failed to screenshot: ", e)
                time.sleep(5)

        except KeyboardInterrupt:
            print("Screenshot loop stopped by user.")


if __name__ == "__main__":
    try:
        while True:
            if isAppActive(target_app):
                print(f"{target_app} is running. Starting screenshot loop.")
                screenshotLoop()
            else:
                print(f"{target_app} is not running.")
                time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user.") 
        