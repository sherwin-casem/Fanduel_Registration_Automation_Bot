import pyautogui
import subprocess
import time
import os
import random

from fundrel_automation.core.env import load_env

ENV = load_env()


def env_value(name, default=""):
    return os.getenv(name) or ENV.get(name, default)
# NOTE: Ensure you have installed opencv for the confidence parameter to work:
# pip install opencv-python

# --- HUMAN-LIKE HELPER FUNCTIONS ---

def human_type(text):
    """Types out text with a random human-like delay between keystrokes."""
    for char in text:
        pyautogui.write(char)
        # Random delay between 0.05 and 0.15 seconds per keypress
        time.sleep(random.uniform(0.05, 0.15))

def human_click_image(image_path, confidence_level=0.8):
    """
    Looks for an image on screen, moves the mouse slowly to it, and clicks.
    confidence_level=0.8 requires opencv-python installed.
    """
    print(f"Looking for {image_path} on screen...")
    try:
        # Find the center of the image on the screen
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)
        
        if location is not None:
            # Move the mouse slowly to the target (taking 0.5 to 1.5 seconds)
            move_duration = random.uniform(0.5, 1.5)
            
            # easeOutQuad makes the mouse movement look more natural
            pyautogui.moveTo(location.x, location.y, duration=move_duration, tween=pyautogui.easeOutQuad)
            
            # Add a tiny human hesitation before clicking
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.click()
            print(f"Successfully clicked {image_path}")
            return True
        else:
            print(f"Could not find {image_path}")
            return False
            
    except pyautogui.ImageNotFoundException:
        print(f"Could not find {image_path}")
        return False

# -----------------------------------

def open_with_proxy(browser="chrome"):
    # The login page you want to open
    url = env_value("FUNDREL_DEMO_URL", "https://example.com")
    
    # Proxy details
    proxy_server = env_value("FUNDREL_PROXY_SERVER", "http://proxy.example.com:10001")

    # Determine browser executable path (Default Windows paths)
    if browser == "chrome":
        browser_path = r"C:\Users\UK-PC\AppData\Local\Google\Chrome\Application\chrome.exe"
        
    elif browser == "edge":
        browser_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    else:
        print("Unsupported browser specified.")
        return

    if not os.path.exists(browser_path):
        print(f"Error: Could not find {browser} at {browser_path}")
        return

    print(f"Launching {browser} with proxy settings...")
    
    # Launch browser in Incognito/InPrivate to ensure it starts a fresh session
    # and doesn't just open a tab in an existing window (which might ignore proxy args)
    if browser == "chrome":
        subprocess.Popen([browser_path, '--incognito', f'--proxy-server={proxy_server}', url])
    else:
        subprocess.Popen([browser_path, '--inprivate', f'--proxy-server={proxy_server}', url])

    print("Waiting 5 seconds for the browser to open...")
    time.sleep(5)

    # --- EMAIL LOGIN PROCESS ---
    
    print("Waiting 8 seconds for the Google login page to fully load...")
    time.sleep(8)
    
    # Step 1: Click the email input field and type the email
    if human_click_image('email.png'):
        human_type(env_value("FUNDREL_DEMO_EMAIL", "person@example.com"))
        
        time.sleep(random.uniform(1.0, 2.0))
        human_click_image('next.png')
        
        print("Waiting 4 seconds for the password page to load...")
        time.sleep(4)
        
        if human_click_image('password.png'):
            human_type(env_value("FUNDREL_DEMO_PASSWORD", "example-password"))
            
            time.sleep(random.uniform(0.5, 1.0))
            human_click_image('next.png')
            
            print("Login process completed!")
        else:
            print("Failed to find the password field. Stopping.")
    else:
        print("Failed to find the email input field. Stopping.")

if __name__ == "__main__":
    # You can change "chrome" to "edge" here
    open_with_proxy("chrome")
