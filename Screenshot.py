import os
import mss
from datetime import datetime
import time
import requests
SERVER_URL = "http://127.0.0.1:3000/upload"  # Replace <SERVER_IP> with server IP

def screenshotLop():
    with mss.mss() as sct:
        folder = "screenshots"
        os.makedirs(folder, exist_ok=True)
        try:
            while True: 
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(folder, f"screenshot_{timestamp}.png")	
                sct.shot(output=filename)
                print(f"Saved {filename}")
                try: 
                    with open(filename, "rb") as f:
                        files = {"image": f}
                        response = requests.post(SERVER_URL, files=files)
                        print("server response:", response.text)
                except Exception as e: 
                    print("Failed to screenshot: ", e)
                time.sleep(5)
        except KeyboardInterrupt:
            print("Screenshot loop stopped by user.")


if __name__ == "__main__":
    screenshotLop()	