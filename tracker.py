import os
import time
import requests
import pygetwindow as gw

# --- CONFIGURATION ---
SERVER_URL = "http://127.0.0.1:8000/Users/receive_activity/"
CONFIG_FILE = ".user_config"
INTERVAL = 30  # Seconds between logs

def get_current_user_from_config():
    """Reads the username currently stored in the config file by Django."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"[!] Error reading config: {e}")
    return ""

def get_active_window_data():
    """Captures the current active window title and app name."""
    try:
        window = gw.getActiveWindow()
        if window and window.title:
            full_title = window.title
            # Extract app name (usually the last part after the hyphen)
            app_name = full_title.split(" - ")[-1] if " - " in full_title else full_title
            return app_name, full_title
    except Exception:
        pass
    return "Idle", "No active window detected"

def run_tracker():
    print("--- AI Procrastination Tracker: OS Agent ---")
    print(f"Status: Waiting for browser login...")

    last_user = ""

    while True:
        # 1. Check who is logged in via the config file
        username = get_current_user_from_config()

        if not username:
            if last_user != "":
                print("\n[SESSION ENDED] User logged out. Waiting for login...")
                last_user = ""
            time.sleep(5) # Check again sooner if no one is logged in
            continue

        if username != last_user:
            print(f"\n[SESSION STARTED] Linked to user: {username}")
            print(f"Monitoring active... (Interval: {INTERVAL}s)")
            last_user = username

        # 2. Capture Activity
        app, title = get_active_window_data()
        
        # 3. Filter out system UI elements
        ignored_elements = ["", "Task Switching", "Windows Input Experience", "Taskbar", "Idle"]
        
        if app not in ignored_elements:
            payload = {
                "username": username,
                "app_name": app,
                "window_title": title,
                "duration": INTERVAL
            }

            try:
                response = requests.post(SERVER_URL, json=payload, timeout=5)
                
                if response.status_code == 201:
                    print(f"[ACTIVE: {username}] Logged: {app} | Window: {title[:30]}...")
                elif response.status_code == 404:
                    print(f"[ERR] 404: Check if SERVER_URL matches your urls.py")
                else:
                    print(f"[ERR] Server Status: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print("[!] Server offline. Retrying...")
            except Exception as e:
                print(f"[!] Unexpected Error: {e}")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        run_tracker()
    except KeyboardInterrupt:
        print("\nTracker stopped by user. Goodbye!")