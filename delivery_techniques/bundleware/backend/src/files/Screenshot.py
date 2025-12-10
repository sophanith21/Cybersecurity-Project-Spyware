import os
import mss
import time
import requests
from datetime import datetime
import pygetwindow as gw # Library to interact with OS windows
import psutil            # Library to interact with OS processes

SERVER_URL = "http://127.0.0.1:3000/upload"
TARGET_APPLICATIONS = ["Chrome", "Firefox", "Edge"] # Keywords in the window title

def is_target_app_active():
    """Checks if a browser window is currently in focus."""
    try:
        # Get the window object that is currently in focus
        active_window = gw.getActiveWindow()
        
        # Check if a window is active and has a title
        if active_window and active_window.title:
            window_title = active_window.title
            
            # Check if any of the target keywords are in the window title
            for app in TARGET_APPLICATIONS:
                if app.lower() in window_title.lower():
                    print(f"Active window: {window_title} - Taking screenshot.")
                    return True
        
        return False
        
    except Exception as e:
        # Handles cases where there is no active window (e.g., on a lock screen)
        print(f"Error checking active window: {e}")
        return False

def screenshotLop_conditional():
    with mss.mss() as sct:
        folder = "screenshots_conditional"
        os.makedirs(folder, exist_ok=True)
        print("Starting conditional screenshot loop...")
        try:
            while True:
                if is_target_app_active():
                    # --- Screenshot and Upload Logic (Only if condition is True) ---
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = os.path.join(folder, f"screenshot_{timestamp}.png")
                    
                    sct.shot(output=filename)
                    print(f"Saved {filename}")
                    
                    try:
                        with open(filename, "rb") as f:
                            files = {"image": f}
                            response = requests.post(SERVER_URL, files=files)
                            print("Server response:", response.text)
                    except Exception as e:
                        print("Failed to upload screenshot:", e)
                    # ----------------------------------------------------------------
                else:
                    print("Browser not in focus. Skipping screenshot.")

                time.sleep(5) # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("Conditional screenshot loop stopped by user.")


if __name__ == "__main__":
    screenshotLop_conditional()