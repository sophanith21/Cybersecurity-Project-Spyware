# startup_monitor_simple.py
import os
import time
import winshell

class StartupMonitor:
    def __init__(self):
        self.startup_folder = winshell.startup()
        self.known_shortcuts = set()
        
        print(f"🔍 Monitoring: {self.startup_folder}")
    
    def analyze_shortcut(self, shortcut_path):
        """Check if shortcut is suspicious"""
        try:
            with winshell.shortcut(shortcut_path) as link:
                target_path = link.path
                
                if not os.path.exists(target_path):
                    return True, target_path, "Target doesn't exist"
                
                if os.path.exists(target_path):
                    return True, target_path, "Target exist"

                return False, target_path, "Looks safe"
                
        except Exception as e:
            return True, "", f"Error: {e}"
    
    def remove_malicious(self, shortcut_path, target_path, reason):
        """Remove both shortcut and target file"""
        try:
            # Remove shortcut
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"🗑️  Removed shortcut: {os.path.basename(shortcut_path)}")
            
            # Remove target
            if os.path.exists(target_path):
                os.remove(target_path)
                print(f"🗑️  Removed target: {os.path.basename(target_path)}")
            
            print(f"🚫 Blocked: {reason}")
            
        except Exception as e:
            print(f"❌ Failed to remove: {e}")
    
    def scan_folder(self):
        """Scan for new shortcuts and check them"""
        if not os.path.exists(self.startup_folder):
            return
        
        current_items = os.listdir(self.startup_folder)
        current_shortcuts = {item for item in current_items if item.endswith('.lnk')}
        
        # Find new shortcuts
        new_shortcuts = current_shortcuts - self.known_shortcuts
        
        for shortcut_name in new_shortcuts:
            shortcut_path = os.path.join(self.startup_folder, shortcut_name)
            print(f"🔎 Checking: {shortcut_name}")
            
            is_suspicious, target_path, reason = self.analyze_shortcut(shortcut_path)
            
            if is_suspicious:
                self.remove_malicious(shortcut_path, target_path, reason)
            else:
                print(f"✅ Safe: {reason}")
                self.known_shortcuts.add(shortcut_name)
        
        # Update known shortcuts
        self.known_shortcuts = current_shortcuts
    
    def run_monitor(self):
        """Main monitoring loop"""
        print("🚀 Startup Monitor Started")
        print("Press Ctrl+C to stop")
        print("-" * 40)
        
        # Load existing shortcuts
        if os.path.exists(self.startup_folder):
            for item in os.listdir(self.startup_folder):
                if item.endswith('.lnk'):
                    self.known_shortcuts.add(item)
        
        try:
            while True:
                self.scan_folder()
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped")

if __name__ == "__main__":
    monitor = StartupMonitor()
    monitor.run_monitor()