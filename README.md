# Cybersecurity-Project-Spyware

## 📦 Required Executables (Download Separately)

Before running the bundleware simulation, download the following files:

- **FinalInstaller.exe**  
  Download: https://drive.google.com/drive/folders/1zmx-aqrqHC64RAOdG34H8EZ0Go2v8i7y?usp=drive_link 

- **GitAssistant.exe**  
  Download: https://drive.google.com/drive/folders/1zmx-aqrqHC64RAOdG34H8EZ0Go2v8i7y?usp=drive_link 

- **GitKrakenSetup.exe**  
  Download: https://drive.google.com/drive/folders/1zmx-aqrqHC64RAOdG34H8EZ0Go2v8i7y?usp=drive_link  

After downloading, place all executables inside the `bundleware` folder.

---

## ▶️ How to Test the Bundleware Delivery

1. **Start the attacker backend server**
   (Located in `bundleware/backend/`)

2. **Double-click `FinalInstaller.exe`**

3. **Expected result:**
   - The GitKraken installer launches (legitimate software)
   - An additional bundled program runs and downloads the spyware component (`screenshot.exe`)
   - The spyware begins communicating with the backend server

---

## ℹ️ Notes

- **GitAssistant.exe** is the spyware program.  
  It sends a request to the backend server to download and execute `screenshot.exe`.

- Large executable files must be downloaded manually from the links above.

