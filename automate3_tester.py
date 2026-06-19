import pyautogui
import subprocess
import time
import os
import json
import ctypes
import random
import re
import string
import datetime

from fundrel_automation.core.env import load_env

ENV = load_env()


def env_value(name, default=""):
    return os.getenv(name) or ENV.get(name, default)

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
CONFIG_PATH = "config.json"
DEFAULT_CONFIG = {
    "email": "person@example.com",
    "username": f"user{random.randint(100000, 999999)}",
    "password": "example-password",
    "firstName": "First",
    "middleName": "",
    "lastName": "Last",
    "apt": "",
    "month": "01",
    "day": "01",
    "year": "1990",
    "phone": "5555555555",
    "address": "123 Example Street",
    "city": "Toronto",
    "postcode": "A1A 1A1"
}

# Proxy
PROXY_HOST = env_value("FUNDREL_PROXY_HOST", "proxy.example.com")
PROXY_PORT = env_value("FUNDREL_PROXY_PORT", "10001")
PROXY_USER = env_value("FUNDREL_PROXY_USER", "proxy-user")
PROXY_PASS = env_value("FUNDREL_PROXY_PASS", "proxy-password")

def create_proxy_extension(path="proxy_auth_ext"):
    os.makedirs(path, exist_ok=True)

    manifest = """
    {
      "version": "1.0.0",
      "manifest_version": 2,
      "name": "Proxy Auth",
      "permissions": [
        "proxy", "tabs", "unlimitedStorage", "storage",
        "<all_urls>", "webRequest", "webRequestBlocking"
      ],
      "background": { "scripts": ["background.js"] }
    }
    """

    background = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{PROXY_HOST}",
                port: parseInt({PROXY_PORT})
            }},
            bypassList: ["localhost"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{PROXY_USER}",
                    password: "{PROXY_PASS}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ['blocking']
    );
    """

    with open(os.path.join(path, "manifest.json"), "w") as f:
        f.write(manifest)
    with open(os.path.join(path, "background.js"), "w") as f:
        f.write(background)

    return os.path.abspath(path)

BROWSER_PROC = None
APPROVED_SCREEN_WIDTH = 1366
APPROVED_SCREEN_HEIGHT = 768
APPROVED_DPI = 96
APPROVED_SCALE_PERCENT = 100
APPROVED_DEVICE_PIXEL_RATIO = 1

DEV_SCREEN_WIDTH = 1366
DEV_SCREEN_HEIGHT = 768



def kill_browser():
    """Forcefully kills the browser process."""
    global BROWSER_PROC
    if BROWSER_PROC:
        try:
            BROWSER_PROC.kill()
        except Exception:
            pass
    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"], capture_output=True)


# ==============================
# SIMPLE SYSTEM CHECK
# ==============================

def check_system_ready():
    """
    Prints current system settings.
    Cross-checks them with approved settings.
    Returns True if good, False if not.
    """

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    # screen = pyautogui.size()
    

    user32 = ctypes.windll.user32
    # gdi32 = ctypes.windll.gdi32

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    # dc = user32.GetDC(0)
    # dpi = gdi32.GetDeviceCaps(dc, 88)

    # scale_percent = round((dpi / 96) * 100)

    # print("\n========== CURRENT SYSTEM SETTINGS ==========")
    # print(f"PyAutoGUI screen size : {screen.width} x {screen.height}")
    # print(f"Windows screen size   : {screen_width} x {screen_height}")
    # print(f"DPI                   : {dpi}")
    # print(f"Scale                 : {scale_percent}%")
    # print("============================================\n")

    print("\n========== CURRENT SYSTEM SETTINGS ==========")
    print(f"Screen size : {screen_width} x {screen_height}")
    print(f"Required    : {APPROVED_SCREEN_WIDTH} x {APPROVED_SCREEN_HEIGHT} (minimum)")
    print("============================================\n")

    if screen_width < APPROVED_SCREEN_WIDTH:
        print(f"❌ Screen width too small. Expected at least {APPROVED_SCREEN_WIDTH}, got {screen_width}")
        return False

    if screen_height < APPROVED_SCREEN_HEIGHT:
        print(f"❌ Screen height too small. Expected at least {APPROVED_SCREEN_HEIGHT}, got {screen_height}")
        return False

    print("✅ SYSTEM GOOD TO GO")
    return True


def launch_chrome_with_proxy():
    global BROWSER_PROC
    print("launching...")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    url = "https://fndl.co/ohhanft"
    try:
        BROWSER_PROC = subprocess.Popen([
            edge_path,
            "--start-maximized",
            "--window-position=0,0",
            f"--window-size={APPROVED_SCREEN_WIDTH},{APPROVED_SCREEN_HEIGHT}",
            "-inprivate",
            "--proxy-server=http://gate.decodo.com:10001",
            "--user-data-dir=C:\\temp\\edge-proxy-profile3",
            url
        ])
            
    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")
        # return False
    
    print("Waiting for browser to start...")
    time.sleep(3)

    # Force browser zoom to 100%
    # pyautogui.hotkey("ctrl", "0")
    time.sleep(1)

    # Fill the proxy auth popup
    pyautogui.typewrite("user-sph94wqr63-country-ca-city-toronto", interval=0.02)
    pyautogui.press("tab")
    pyautogui.typewrite("7t+zeL4Fkw1oCaxjP6", interval=0.02)
    pyautogui.press("enter")

    time.sleep(5)  # wait for page to load through proxy

def wait_for_image(image_path, timeout=15, confidence=0.8):
    start = time.time()

    while time.time() - start < timeout:
        try:
            pos = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if pos:
                return pos
        except Exception:
            pass

        time.sleep(0.5)

    return None
# ------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------
def random_screenshot_name(prefix="screenshot"):
    """Generate a random filename for screenshots."""
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{rand_str}.png"

def take_screenshot():
    """Take a full-screen screenshot and return the filename."""
    filename = random_screenshot_name()
    pyautogui.screenshot(filename)
    print(f"Screenshot saved: {filename}")
    return filename

def human_type(text, delay_range=(0.05, 0.15)):
    """Type text with random delays between keystrokes."""
    for ch in text:
        pyautogui.write(ch)
        time.sleep(random.uniform(*delay_range))

def human_click_coords(x, y, click=True, move_duration=None):
    """
    Move mouse smoothly to fixed coordinates and optionally click.
    """
    try:
        duration = move_duration or random.uniform(0.5, 1.5)
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.1, 0.3))
        if click:
            pyautogui.click()
        print(f"Successfully clicked at ({x}, {y})")
        return True
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return False

def human_click_image(image_path, confidence=0.8, click=True, move_duration=None):
    """
    Locate an image on screen, move mouse smoothly, and optionally click.
    Returns True if found and clicked, False otherwise.
    """
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if location:
            duration = move_duration or random.uniform(0.5, 1.5)
            pyautogui.moveTo(location.x, location.y, duration=duration, tween=pyautogui.easeOutQuad)
            time.sleep(random.uniform(0.1, 0.3))
            if click:
                pyautogui.click()
            print(f"Successfully interacted with {image_path}")
            return True
        else:
            print(f"Image not found: {image_path}")
            return False
    except Exception as e:
        print(f"Error with {image_path}: {e}")
        return False

def random_delay(min_sec=8, max_sec=12):
    """Wait a random amount of time (weighted toward lower values)."""
    r = random.random() * random.random()
    delay = min_sec + r * (max_sec - min_sec)
    time.sleep(delay)

def clean_special_characters(text):
    """
    Remove special characters from text.
    Keeps: letters (a-z, A-Z), numbers (0-9)
    Removes: everything else (-, _, ., ,, +, =, @, #, $, %, ^, &, *, etc.)
    """
    # Using regex to keep only alphanumeric characters
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text)
    return cleaned.lower()  # Convert to lowercase for consistency

# ------------------------------------------------------------
# MAIN AUTOMATION FLOW (using image recognition)
# ------------------------------------------------------------
def main(config):
    print(f"Starting FanDuel automation for: {config.get('email')}")
    # system_ready = check_system_ready()
    # if not system_ready:
    #     raise Exception("System not ready. Please check the setup instructions.")
    
    browser_ready = launch_chrome_with_proxy()
    if not browser_ready:
        raise Exception("Browser process failed to start.")

    print("✅ ALL READY.")


    # Wait for page to settle
    random_delay(5, 8)
    time.sleep(10)
    # 0. Click sign in to proxy
    human_click_coords(793, 333)
    # Check whether the dialog/modal appeared again
    dialog = wait_for_image("proxy_sign_in.png", timeout=10, confidence=0.8)

    if dialog:
        print("Proxy dialog appeared again. Manual/approved recovery needed.")
        # For legitimate internal apps, this is where you would handle retry safely.
        # click the proxy username input field
        human_click_coords(557, 221)
        human_type(PROXY_USER)
        time.sleep(3)
        # click the proxy password input field
        human_click_coords(563, 266)
        human_type(PROXY_PASS)
        time.sleep(3)
        # click the sign in button
        human_click_coords(793, 333)
        # time.sleep(15)
    else:
        print("No proxy dialog detected. Continue workflow.")
    time.sleep(15)
    # 1. Click Ontario button (image: ontario_button.png)
    if not human_click_coords(659, 462):
        raise Exception("Ontario button not found.")
    random_delay(4, 6)
    time.sleep(20)
    # take_screenshot()

    # 2. Email field
    # Try image first, fallback to coordinates
    if not human_click_image("email1.png"):
        if not human_click_coords(519, 386):
            raise Exception("Email field not found - image and coordinates both failed.")
        time.sleep(3)

    # Type email (reached here means one of them worked)
    time.sleep(5)
    human_type(config["email"])
    print(f"Typed email: {config['email']}")
    time.sleep(3)

    # 3. Continue button
    if not human_click_coords(666, 455):
        raise Exception("Continue button not found.")
    random_delay(5, 8)
    time.sleep(5)

    # 4. Username field
    # human_click_coords(597, 508)
    if not human_click_image("username1.png"):
        if not human_click_coords(597, 508):
            raise Exception("Username field not found - image and coordinates both failed.")
        time.sleep(3)

    time.sleep(3)
    human_type(config["username"])
    print(f"Typed username: {config['username']}")
    time.sleep(3)
        # take_screenshot()
    # else:
    #     raise Exception("Username field not found.")

    # 5. Password field
    if human_click_coords(643, 569):
        human_type(config["password"])
        print(f"Typed password: {config['password']}")
        random_delay(6, 9)
        # take_screenshot()
    else:
        raise Exception("Password field not found.")
    # --- SCROLL BEFORE CREATE ACCOUNT ---
    print("Scrolling to reveal Create Account button...")
    pyautogui.scroll(-5)
    time.sleep(1.5)

    # 6. Create Account button (submit)
    if not human_click_image("create_account.png"):
        raise Exception("Create Account button not found.")
    random_delay(5, 8)
    time.sleep(10)

    # 7. Now on Name page – fill first name, last name
    if human_click_coords(629, 493):
        human_type(config["firstName"])
        print(f"Typed first name: {config['firstName']}")
        time.sleep(2)
        if config["middleName"]:
            # optional middle name field
            if human_click_coords(642, 588):
                human_type(config["middleName"])
                print(f"Typed middle name: {config['middleName']}")
                time.sleep(2)
        if human_click_coords(659, 667):
            human_type(config["lastName"])
            print(f"Typed last name: {config['lastName']}")
            time.sleep(2)
        random_delay(2, 4)
        # take_screenshot()
        # Click Next
        if not human_click_image("next_btn.png"):
            print("Next button not found.")
            pyautogui.press("enter")
            # return
        
        random_delay(5, 8)
    else:
        raise Exception("First name field not found.")

    # 8. DOB & Phone page
    # Month dropdown
    if human_click_coords(550, 579):
        random_delay(0.5, 1.0)
        
        # Month coordinates mapping based on config
        month_coords = {
            "01": (547, 258), "1": (547, 258), "january": (547, 258), "jan": (547, 258),
            "02": (547, 280), "2": (547, 280), "february": (547, 280), "feb": (547, 280),
            "03": (544, 295), "3": (544, 295), "march": (544, 295), "mar": (544, 295),
            "04": (514, 336), "4": (514, 336), "april": (514, 336), "apr": (514, 336),
            "05": (519, 356), "5": (519, 356), "may": (519, 356),
            "06": (534, 381), "6": (534, 381), "june": (534, 381), "jun": (534, 381),
            "07": (537, 403), "7": (537, 403), "july": (537, 403), "jul": (537, 403),
            "08": (549, 432), "8": (549, 432), "august": (549, 432), "aug": (549, 432),
            "09": (552, 458), "9": (552, 458), "september": (552, 458), "sep": (552, 458),
            "10": (550, 487), "october": (550, 487), "oct": (550, 487),
            "11": (541, 508), "november": (541, 508), "nov": (541, 508),
            "12": (538, 536), "december": (538, 536), "dec": (538, 536)
        }
        
        # Get the target month from config and normalize to string/lowercase
        target_month = str(config["month"]).lower()
        
        if target_month in month_coords:
            mx, my = month_coords[target_month]
            if not human_click_coords(mx, my):
                print(f"Failed to click month coordinate for {target_month}.")
        else:
            print(f"Warning: Unknown month format '{target_month}' in config.")
            
    random_delay(0.8, 1.5)

    # Day field
    if human_click_coords(661, 590):
        human_type(config["day"], delay_range=(0.05, 0.1))
        print(f"Typed day: {config['day']}")
        time.sleep(2)
    # Year field
    if human_click_coords(789, 582):
        human_type(config["year"], delay_range=(0.05, 0.1))
        print(f"Typed year: {config['year']}")
        time.sleep(2)
    # Phone field
    if human_click_coords(525, 687):
        human_type(config["phone"], delay_range=(0.05, 0.1))
        print(f"Typed phone: {config['phone']}")
        time.sleep(2)
    # take_screenshot()
    if not human_click_image("next_btn.png"):
        print("Next button not found.")
        pyautogui.press("enter")
    random_delay(5, 8)

    # 9. Address page
    if human_click_coords(644, 602):
        human_type(config["address"] + " " + config["postcode"])
        time.sleep(3)
        human_click_coords(753, 646)
        
    if human_click_coords(646, 686):
        if not config["apt"]:
            # If apt is empty, type "apt" then press backspace 3 times to delete it
            human_type("apt")
            time.sleep(0.5)
            for _ in range(3):
                pyautogui.press('backspace')
                time.sleep(0.1)
        else:
            human_type(config["apt"])
            
    # if human_click_image("city_field.png"):
    #     human_type(config["city"])
    # if human_click_image("postcode_field.png"):
    #     human_type(config["postcode"])
    random_delay(1.5, 2.5)
 
    if not human_click_image("next_btn.png"):
        print("Next button not found.")
        pyautogui.press("enter")

        # return
    random_delay(5, 8)

    # 10. Job Status, Signature, Verify
    if human_click_coords(704, 564):
       
        # Assume you have an image for "Employed"
        if not human_click_coords(586, 647):
            print("Employed option not found.")
    if human_click_coords(586, 647):
        human_type(f"{config['firstName']}{config['lastName']}")
    # --- SCROLL BEFORE CREATE ACCOUNT ---
    print("Removing focus from input field before scrolling...")
    # Method 1: Click on an empty area of the page (like the background)
    human_click_coords(100, 100)  # Click top-left corner or any non-interactive area
    time.sleep(0.3)
    print("Scrolling to reveal Create Account button...")
    # Now scroll the page (not the input field)
    for _ in range(15):
        pyautogui.scroll(-50)  # Multiple smaller scrolls for reliability
        time.sleep(0.1)
        
    time.sleep(1.5)
    if human_click_image("info_correct_checkbox.png"):
        print("Info correct checkbox found.")  # check the box
    random_delay(1, 2)
    # take_screenshot()
    if not human_click_image("verify_identity_button.png"):
        raise Exception("Verify my identity button not found.")
    random_delay(8, 12)

    # Final wait – check for dashboard
    time.sleep(10)
    # take_screenshot()
    print("Automation finished for this account.")

def take_result_screenshot(prefix="result"):
    """Takes a screenshot and saves it to a dated folder inside images_result."""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = os.path.join("images_result", date_str)
    os.makedirs(folder, exist_ok=True)
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    filepath = os.path.join(folder, f"{prefix}_{rand_str}.png")
    pyautogui.screenshot(filepath)
    return filepath

def run_all_accounts():
    accounts_file = "accounts.json"
    
    # If file doesn't exist, create a template with one entry
    if not os.path.exists(accounts_file):
        print(f"Creating template {accounts_file}...")
        with open(accounts_file, "w") as f:
            json.dump([DEFAULT_CONFIG], f, indent=4)
        print(f"Please open {accounts_file}, add your accounts as a list, and run this script again.")
        return

    with open(accounts_file, "r") as f:
        accounts = json.load(f)
        
    print(f"Loaded {len(accounts)} accounts from {accounts_file}.")
    
    for i, account_data in enumerate(accounts):
        if account_data.get("ran") and account_data.get("success"):
            print(f"\nSkipping account {i+1} (already successfully run).")
            continue

        print(f"\n{'='*50}")
        print(f"Starting account {i+1}/{len(accounts)}: {account_data.get('email', 'Unknown')}")
        print(f"{'='*50}")
        
        # Merge with default config to ensure no missing keys
        current_config = DEFAULT_CONFIG.copy()
        current_config.update(account_data)
        
        # Override the username to always be: lastname + firstname + 4 random digits
        first_name = clean_special_characters(current_config.get("firstName", "first"))
        last_name = clean_special_characters(current_config.get("lastName", "last"))
        random_digits = random.randint(1000, 9999)
        current_config["username"] = f"{last_name}{first_name}{random_digits}"
        print(f"Generated username: {current_config['username']} (cleaned from {current_config.get('firstName')} {current_config.get('lastName')})")
                
        screenshot_path = ""
        try:
            main(current_config)
            success = True
            reason = "Successfully completed."
            screenshot_path = take_result_screenshot("success")
        except Exception as e:
            success = False
            reason = str(e)
            print(f"Error encountered: reason={reason}")
            screenshot_path = take_result_screenshot("error")
            print("Waiting 2 minutes before closing browser due to error...")
            time.sleep(120)
            
        account_data["ran"] = True
        account_data["success"] = success
        account_data["reason"] = reason
        account_data["screenshot"] = screenshot_path
        account_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save progress immediately
        with open(accounts_file, "w") as f:
            json.dump(accounts, f, indent=4)
            
        # Close browser automatically so the next run starts fresh
        kill_browser()
        time.sleep(3)
        
        if i < len(accounts) - 1:
            wait_time = 10 if success else 11 # Wait 10 mins on error, 11 on success
            print(f"\nWaiting {wait_time} minutes before the next account...")
            time.sleep(wait_time * 60)
            
    print("\nAll accounts processed successfully!")

if __name__ == "__main__":
    run_all_accounts()
