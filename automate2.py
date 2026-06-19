import pyautogui
import subprocess
import time
import os
import random
import string
import datetime

from fundrel_automation.core.accounts import (
    clean_special_characters as clean_account_text,
    load_accounts,
    prepare_account_config,
    save_accounts,
    validate_account as validate_account_data,
)
from fundrel_automation.core.config import load_settings, save_settings
from fundrel_automation.core.errors import AccountAlreadyExists, AutomationError, AutomationStopped
from fundrel_automation.core.logging_config import get_logger
from fundrel_automation.core.paths import ACCOUNTS_PATH, RESULTS_DIR, asset_path
from fundrel_automation.core.results import (
    RESULT_CREATED,
    RESULT_SERVICE_NOT_AVAILABLE,
    RESULT_SUCCESS_NOT_CREATED,
    RESULT_UNABLE_TO_VERIFY,
    RESULT_WE_FOUND_ANOTHER_ACCOUNT,
    apply_outcome_to_account,
    outcome_from_exception,
    outcome_from_result,
)
from fundrel_automation.core.routing import select_url_and_proxy

logger = get_logger(__name__)


def log_message(*values, sep=" ", end="\n", **_kwargs):
    message = sep.join(str(value) for value in values)
    if end and end != "\n":
        message += end
    logger.info(message.rstrip("\n"))


print = log_message

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
# Global stop flag
STOP_REQUESTED = False

def set_stop_requested(value):
    global STOP_REQUESTED
    STOP_REQUESTED = value

def check_stop():
    global STOP_REQUESTED
    if STOP_REQUESTED:
        raise AutomationStopped()

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
    "province": "ON",
    "postcode": "A1A 1A1"
}

def get_next_url_and_proxy(settings, account_config=None):
    url, proxy, min_wait = select_url_and_proxy(settings, account_config)
    save_settings(settings)
    return url, proxy, min_wait

def validate_account(config):
    return validate_account_data(config)
BROWSER_PROC =None
def kill_browser():
    """Forcefully kills the browser process."""
    global BROWSER_PROC

    if BROWSER_PROC:
        try:
            BROWSER_PROC.kill()
        except Exception:
            pass
    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"], capture_output=True)
    
    # Wait to ensure processes are fully terminated before trying to delete files
    time.sleep(3)
    
    # Delete the temporary Edge profile directory
    profile_dir = r"C:\temp\edge-proxy-profile3"
    if os.path.exists(profile_dir):
        try:
            import shutil
            shutil.rmtree(profile_dir, ignore_errors=True)
            print(f"Deleted temporary profile: {profile_dir}")
        except Exception as e:
            print(f"Could not fully delete profile directory: {e}")

def launch_chrome_with_proxy(url, proxy=None):
    global BROWSER_PROC
    print(f"launching with URL: {url}")
    
    settings = load_settings()
    edge_path = settings.get("edge_path", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

    args = [
        edge_path,
        # "--start-maximized",
        "--window-position=0,0",
        "--window-size=1366,768",
        "-inprivate",
        "--user-data-dir=C:\\temp\\edge-proxy-profile3",
        url
    ]
    
    if proxy:
        args.insert(4, f"--proxy-server=http://{proxy['host']}:{proxy['port']}")

    BROWSER_PROC = subprocess.Popen(args)
    print("Waiting for browser to start...")
    time.sleep(3)

    if proxy:
        # Fill the proxy auth popup
        pyautogui.typewrite(proxy['user'], interval=0.02)
        pyautogui.press("tab")
        pyautogui.typewrite(proxy['pass'], interval=0.02)
        pyautogui.press("enter")

    time.sleep(5)  # wait for page to load

def wait_for_image(image_path, timeout=15, confidence=0.8):
    image_path = str(asset_path(image_path))
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
    check_stop()
    filename = str(RESULTS_DIR / random_screenshot_name())
    os.makedirs(RESULTS_DIR, exist_ok=True)
    pyautogui.screenshot(filename)
    print(f"Screenshot saved: {filename}")
    return filename

def human_type(text, delay_range=(0.05, 0.15)):
    """Type text with random delays between keystrokes."""
    check_stop()
    for ch in text:
        check_stop()
        pyautogui.write(ch)
        time.sleep(random.uniform(*delay_range))

def human_click_coords(x, y, click=True, move_duration=None):
    """
    Move mouse smoothly to fixed coordinates and optionally click.
    """
    check_stop()
    try:
        duration = move_duration or random.uniform(0.5, 1.5)
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)
        check_stop()
        time.sleep(random.uniform(0.1, 0.3))
        check_stop()
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
    check_stop()
    image_path = str(asset_path(image_path))
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        check_stop()
        if location:
            duration = move_duration or random.uniform(0.5, 1.5)
            pyautogui.moveTo(location.x, location.y, duration=duration, tween=pyautogui.easeOutQuad)
            check_stop()
            time.sleep(random.uniform(0.1, 0.3))
            check_stop()
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
    check_stop()
    r = random.random() * random.random()
    delay = min_sec + r * (max_sec - min_sec)
    # Sleep in small increments to allow checking stop flag
    start = time.time()
    while time.time() - start < delay:
        check_stop()
        time.sleep(0.1)

def clean_special_characters(text):
    return clean_account_text(text)

def clear_and_type(text, backspace_count=20):
    """Backspace to clear a field, then type the new text."""
    check_stop()
    for _ in range(backspace_count):
        check_stop()
        pyautogui.press('backspace')
        time.sleep(0.01)
    human_type(text)

def click_image_or_coord(image_path, x, y, confidence=0.8):
    """Try to click an image, if not found, fallback to coordinates."""
    if not human_click_image(image_path, confidence=confidence):
        human_click_coords(x, y)

def image_on_screen(image_path, confidence=0.8):
    """Return True when the named project image asset is visible on screen."""
    try:
        return pyautogui.locateOnScreen(str(asset_path(image_path)), confidence=confidence) is not None
    except Exception:
        return False

# ------------------------------------------------------------
# MAIN AUTOMATION FLOW (using image recognition)
# ------------------------------------------------------------
def main(config, url, proxy=None):
    print(f"Starting FanDuel automation for: {config.get('email')}")
    check_stop()
    launch_chrome_with_proxy(url, proxy)

    # Wait for page to settle
    random_delay(5, 8)
    check_stop()
    time.sleep(10)
    
    if proxy:
        # 0. Click sign in to proxy
        human_click_coords(793, 333)
        # Check whether the dialog/modal appeared again
        dialog = wait_for_image("proxy_sign_in.png", timeout=15, confidence=0.8)

        if dialog:
            print("Proxy dialog appeared again. Manual/approved recovery needed.")
            # For legitimate internal apps, this is where you would handle retry safely.
            # click the proxy username input field
            human_click_coords(557, 221)
            human_type(proxy['user'])
            check_stop()
            time.sleep(3)
            # click the proxy password input field
            human_click_coords(563, 266)
            human_type(proxy['pass'])
            check_stop()
            time.sleep(3)
            # click the sign in button
            human_click_coords(793, 333)
            # time.sleep(15)
        else:
            print("No proxy dialog detected. Continue workflow.")
        check_stop()
        time.sleep(15)
    else:
        print("No proxy provided. Continue workflow.")
        check_stop()
        time.sleep(10)
    # 1. Click Ontario button (image: ontario_button.png)
    if not human_click_coords(659, 462):
        raise AutomationError("Ontario button not found.")
    random_delay(4, 6)
    check_stop()
    time.sleep(25)
    # take_screenshot()

    # 2. Email field
    # Try image first, fallback to coordinates
    
    
    if not human_click_image("email1.png"):
        if not human_click_coords(519, 386):
            raise AutomationError("Email field not found - image and coordinates both failed.")
        time.sleep(3)

    # Type email (reached here means one of them worked)
    check_stop()
    time.sleep(5)
    human_type(config["email"])
    print(f"Typed email: {config['email']}")
    check_stop()
    time.sleep(3)

    # 3. Continue button
    if not human_click_coords(666, 455):
        raise AutomationError("Continue button not found.")
    random_delay(5, 8)
    check_stop()
    time.sleep(5)
    
    # Check if login image appears, meaning account already exists
    print("Checking if account already exists...")
    check_stop()
    if image_on_screen("login.png", confidence=0.8):
        print("Login prompt appeared, account already exists.")
        raise AccountAlreadyExists()
    print("Login image not found. Proceeding with registration...")

    # 4. Username field
    check_stop()
    time.sleep(5)
    # human_click_coords(597, 508)
    if not human_click_image("username1.png"):
        if not human_click_coords(597, 508):
            raise AutomationError("Username field not found - image and coordinates both failed.")
        time.sleep(3)

    check_stop()
    time.sleep(3)
    human_type(config["username"])
    print(f"Typed username: {config['username']}")
    check_stop()
    time.sleep(3)
        # take_screenshot()

    # 5. Password field
    check_stop()
    if human_click_coords(643, 569):
        human_type(config["password"])
        print(f"Typed password: {config['password']}")
        check_stop()
        random_delay(6, 9)
        # take_screenshot()
    else:
        raise AutomationError("Password field not found.")
    # --- SCROLL BEFORE CREATE ACCOUNT ---
    print("Scrolling to reveal Create Account button...")
    check_stop()
    pyautogui.scroll(-5)
    check_stop()
    time.sleep(1.5)

    # 6. Create Account button (submit)
    if not human_click_image("create_account.png"):
        raise AutomationError("Create Account button not found.")
    
    print("Waiting to see if 'service not available' appears...")
    start_wait = time.time()
    service_unavailable = False
    
    while time.time() - start_wait < 15:
        if image_on_screen("service_unavailable.png", confidence=0.8):
            service_unavailable = True
            break
            
        # Check if we moved to the next page successfully
        if image_on_screen("firstname_field.png", confidence=0.8):
            break
            
        time.sleep(1)

    if service_unavailable:
        print("Service not available page detected. Ending for this account.")
        take_result_screenshot(prefix="service_not_available")
        return False, RESULT_SERVICE_NOT_AVAILABLE
        
    random_delay(2, 4)
    time.sleep(2)

    # 7. Now on Name page – fill first name, last name
    for attempt in range(2):
        print(f"Name Page - Attempt {attempt + 1}")
        
        click_image_or_coord("firstname_field.png", 629, 493)
        clear_and_type(config["firstName"], len(config["firstName"]) + 10)
        print(f"Typed first name: {config['firstName']}")
        time.sleep(2)
        
        if config["middleName"]:
            click_image_or_coord("middlename_field.png", 642, 588)
            clear_and_type(config["middleName"], len(config["middleName"]) + 10)
            print(f"Typed middle name: {config['middleName']}")
            time.sleep(2)
            
        click_image_or_coord("lastname_field.png", 659, 667)
        clear_and_type(config["lastName"], len(config["lastName"]) + 10)
        print(f"Typed last name: {config['lastName']}")
        time.sleep(2)
        
        random_delay(2, 4)
        if not human_click_image("next_btn.png"):
            print("Next button not found.")
            pyautogui.press("enter")
            
        random_delay(5, 8)
        
        # Verify if it went through by checking if firstname field is still there
        if not wait_for_image("firstname_field.png", timeout=7):
            print("Name page successful, moving to next.")
            break
        print("Name page failed to advance, retrying...")
    else:
        raise AutomationError("Failed to pass Name page after 2 attempts.")

    # 8. DOB & Phone page
    for attempt in range(2):
        print(f"DOB & Phone Page - Attempt {attempt + 1}")
        
        # Month
        if attempt == 0:
            click_image_or_coord("month_field.png", 550, 579)
            month_str = str(config["month"]).lower()
            # Convert "11" to "nov", "01" to "jan", etc. if it's numeric
            month_map = {"01":"jan","1":"jan","02":"feb","2":"feb","03":"mar","3":"mar","04":"apr","4":"apr","05":"may","5":"may","06":"jun","6":"jun","07":"jul","7":"jul","08":"aug","8":"aug","09":"sep","9":"sep","10":"oct","11":"nov","12":"dec"}
            short_month = month_map.get(month_str, month_str[:3])
            clear_and_type(short_month, 5)
            time.sleep(1)
        else:
            click_image_or_coord("month_field.png", 550, 579)
            random_delay(0.5, 1.0)
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
            target_month = str(config["month"]).lower()
            if target_month in month_coords:
                mx, my = month_coords[target_month]
                human_click_coords(mx, my)
            time.sleep(1)

        # Day field
        click_image_or_coord("day_field.png", 661, 590)
        clear_and_type(config["day"], 5)
        print(f"Typed day: {config['day']}")
        time.sleep(2)
        
        # Year field
        click_image_or_coord("year_field.png", 789, 582)
        clear_and_type(config["year"], 6)
        print(f"Typed year: {config['year']}")
        time.sleep(2)
        
        # Phone field
        click_image_or_coord("phone_field.png", 525, 687)
        clear_and_type(config["phone"], 15)
        print(f"Typed phone: {config['phone']}")
        time.sleep(2)
        
        print("Scrolling down to reveal Next button...")
        pyautogui.scroll(-200)
        time.sleep(1)
        
        if not human_click_image("next_btn.png"):
            print("Next button not found.")
            pyautogui.press("enter")
        random_delay(5, 8)
        
        if not wait_for_image("month_field.png", timeout=3):
            print("DOB & Phone page successful, moving to next.")
            break
        print("DOB & Phone page failed to advance, retrying with fallback...")
    else:
        raise AutomationError("Failed to pass DOB & Phone page after 2 attempts.")

    # 9. Address page
    for attempt in range(2):
        print(f"Address Page - Attempt {attempt + 1}")
        if attempt == 0:
            click_image_or_coord("address_field.png", 644, 602)
            human_type(f"{config['address']} {config['city']} {config['postcode']}")
            time.sleep(3)
            human_click_coords(753, 646) # Follow Google suggestion coord
            
            click_image_or_coord("apt1.png", 646, 686)
            if not config.get("apt"):
                human_type("apt")
                time.sleep(0.5)
                for _ in range(3): pyautogui.press('backspace'); time.sleep(0.1)
            else:
                human_type(config["apt"])
        else:
            print("Retrying address page with manual postcode fallback...")
            click_image_or_coord("address_field.png", 644, 602)
            clear_and_type(f"{config['address']} {config['city']} {config['postcode']}", 55)
            time.sleep(3)
            human_click_coords(753, 646) # Click suggestion
            
            print("Clicking empty space and scrolling...")
            human_click_coords(100, 100) # Click empty space
            time.sleep(0.5)
            pyautogui.scroll(-200) # Scroll down
            time.sleep(1)
            
            click_image_or_coord("postcode_field.png", 646, 750) # Fallback coord for postcode
            clear_and_type(config["postcode"], 7)
                
        random_delay(1.5, 2.5)
        if not human_click_image("next_btn.png"):
            print("Next button not found.")
            pyautogui.press("enter")
        random_delay(5, 8)
        
        if not wait_for_image("address_field.png", timeout=3):
            print("Address page successful, moving to next.")
            break
        print("Address field still detected, retrying...")
    else:
        raise AutomationError("Failed to pass Address page after 2 attempts.")

    # 10. Job Status, Signature, Verify
    for attempt in range(2):
        print(f"Job & Signature Page - Attempt {attempt + 1}")
        if attempt == 0:
            click_image_or_coord("job_field.png", 704, 564)
            time.sleep(1)
            if not human_click_image("unemployed_option.png"):
                print("Unemployed option image not found, falling back to coord.")
                human_click_coords(586, 647)
                
            click_image_or_coord("signature_field.png", 586, 647)
            clear_and_type(f"{config['firstName']} {config['lastName']}", 30)
        else:
            print("Retrying Job & Signature page with fallback...")
            # Scroll back up to reset view
            for _ in range(10): pyautogui.scroll(50); time.sleep(0.1)
            time.sleep(1)
            
            human_click_coords(704, 564) # job coord
            time.sleep(1)
            human_click_coords(586, 647) # unemployed option coord
            
            human_click_coords(586, 647) # signature coord
            for _ in range(20): pyautogui.press('right'); time.sleep(0.01)
            for _ in range(30): pyautogui.press('backspace'); time.sleep(0.01)
            human_type(f"{config['firstName']}{config['lastName']}")

        # --- SCROLL BEFORE CREATE ACCOUNT ---
        print("Removing focus from input field before scrolling...")
        human_click_coords(100, 100)  # Click top-left corner
        time.sleep(0.3)
        
        print("Scrolling to reveal Verify button...")
        for _ in range(15):
            pyautogui.scroll(-50)
            time.sleep(0.1)
            
        time.sleep(1.5)
        if human_click_image("info_correct_checkbox.png"):
            print("Info correct checkbox found.")
            
        random_delay(1, 2)
        if human_click_image("verify_identity_button.png"):
            print("Verify identity button clicked successfully.")
            break
        print("Verify my identity button not found, triggering retry...")
    else:
        raise AutomationError("Verify my identity button not found after 2 attempts.")

    # --- FINAL VERIFICATION AND TERMS ACCEPTANCE ---
    print("Waiting for success, 'another account', or 'unable to verify' screen...")
    
    # Wait loop to check for all three images
    start_time = time.time()
    success_found = False
    another_account_found = False
    unable_to_verify_found = False
    
    while time.time() - start_time < 30:
        if image_on_screen("success.png", confidence=0.8):
            success_found = True
            break
            
        if image_on_screen("we_found_another_account.png", confidence=0.8):
            another_account_found = True
            break

        if image_on_screen("we_couldnt_verify_your_data1.png", confidence=0.8):
            unable_to_verify_found = True
            break
            
        time.sleep(1)

    is_created = False
    status = "failed"
    
    if unable_to_verify_found:
        print("'We couldn't verify your data' image detected. Taking screenshot and ending.")
        take_result_screenshot(prefix="unable_to_verify")
        print("Automation finished for this account due to verification failure.")
        return False, RESULT_UNABLE_TO_VERIFY
    
    if another_account_found:
        print("'We found another account' image detected. Taking screenshot and ending.")
        take_result_screenshot(prefix="we_found_another_account")
        # Do not mark as created, but we handled it gracefully.
        print("Automation finished for this account due to finding another account.")
        return False, RESULT_WE_FOUND_ANOTHER_ACCOUNT
    
    if success_found:
        print("Success image found, clicking to accept terms.")
        human_click_image("success.png")
        
        time.sleep(2)
        print("Scrolling down (-200 to -250)...")
        scroll_amount = random.randint(500, 550)
        pyautogui.scroll(-scroll_amount)
        time.sleep(3)
        
        print("Looking for first continue image...")
        if human_click_image("continue1.png", confidence=0.8):
            print("First continue clicked.")
        else:
            print("First continue image not found, proceeding anyway...")
            
        time.sleep(10)
        
        print("Scrolling down again (-200 to -250)...")
        scroll_amount = random.randint(400, 450)
        pyautogui.scroll(-scroll_amount)
        time.sleep(2)
        
        print("Looking for second continue image...")
        if human_click_image("continue1.png", confidence=0.8):
            print("Second continue clicked.")
        else:
            print("Second continue image not found, proceeding anyway...")
            
        time.sleep(15)
        
        print("Scrolling down one last time (-700)...")
        pyautogui.scroll(-700)
        time.sleep(2)
        
        print("Looking for 'do it later' image...")
        if human_click_image("do_it_later.png", confidence=0.8):
            print("'Do it later' clicked.")
            time.sleep(15)
        else:
            print("'Do it later' image not found, proceeding anyway...")
            
        is_created = True
        status = RESULT_CREATED
    else:
        print("Success image not found after verification. Marking as standard success instead of created.")
        status = RESULT_SUCCESS_NOT_CREATED

    print("Automation finished for this account.")
    return is_created, status

def take_result_screenshot(prefix="result"):
    """Takes a screenshot and saves it to a dated folder inside images_result."""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    folder = RESULTS_DIR / date_str
    os.makedirs(folder, exist_ok=True)
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    filepath = folder / f"{prefix}_{rand_str}.png"
    pyautogui.screenshot(filepath)
    return str(filepath)

def run_all_accounts():
    accounts_file = ACCOUNTS_PATH
    
    # If file doesn't exist, create a template with one entry
    if not accounts_file.exists():
        print(f"Creating template {accounts_file}...")
        save_accounts([DEFAULT_CONFIG], accounts_file)
        print(f"Please open {accounts_file}, add your accounts as a list, and run this script again.")
        return

    accounts = load_accounts(accounts_file)
        
    print(f"Loaded {len(accounts)} accounts from {accounts_file}.")
    
    settings = load_settings()
    
    for i, account_data in enumerate(accounts):
        if account_data.get("ran") and account_data.get("success"):
            print(f"\nSkipping account {i+1} (already successfully run).")
            continue

        if account_data.get("skipped"):
            print(f"\nSkipping account {i+1} (marked as skipped: {account_data.get('reason')}).")
            continue

        print(f"\n{'='*50}")
        print(f"Starting account {i+1}/{len(accounts)}: {account_data.get('email', 'Unknown')}")
        print(f"{'='*50}")
        
        current_config = prepare_account_config(account_data, DEFAULT_CONFIG)
        
        is_valid, val_reason = validate_account(current_config)
        if not is_valid:
            print(f"Skipping account {i+1}: {val_reason}")
            account_data["ran"] = True
            account_data["success"] = False
            account_data["skipped"] = True
            account_data["reason"] = val_reason
            account_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_accounts(accounts, accounts_file)
            continue
        
        print(f"Generated username: {current_config['username']} (cleaned from {current_config.get('firstName')} {current_config.get('lastName')})")
                
        url, proxy, wait_time = get_next_url_and_proxy(settings, current_config)
        if wait_time > 0:
            print(f"Proxy cooldown active. Waiting {int(wait_time)} seconds before starting...")
            time.sleep(wait_time)
                
        try:
            is_created, status = main(current_config, url, proxy)
            outcome = outcome_from_result(is_created, status)
                
        except Exception as e:
            outcome = outcome_from_exception(e)
            print(f"Error encountered: {outcome.reason}")
            print("Waiting 2 minutes before closing browser due to error...")
            time.sleep(120)

        screenshot_path = take_result_screenshot(outcome.screenshot_prefix)
        apply_outcome_to_account(
            account_data,
            outcome,
            screenshot_path,
            username=current_config["username"],
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        
        # Save progress immediately
        save_accounts(accounts, accounts_file)
            
        # Close browser automatically so the next run starts fresh
        kill_browser()
        time.sleep(3)
        
        if i < len(accounts) - 1:
            settings = load_settings()
            proxies = settings.get("proxies", [])
            if len(proxies) <= 1:
                wait_time = 10 if outcome.success else 11 # Wait 10 mins on success, 11 on error
                print(f"\nWaiting {wait_time} minutes before the next account...")
                time.sleep(wait_time * 60)
            else:
                print(f"\nMoving to next account (multiple proxies configured).")
                time.sleep(5)
            
    print("\nAll accounts processed successfully!")

if __name__ == "__main__":
    run_all_accounts()
# ------------------------------------------------------------
