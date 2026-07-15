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


def find_matching_image(image_names, confidences=(0.8, 0.7, 0.6)):
    """Return the first visible image name and confidence used, or (None, None)."""
    for image_name in image_names:
        for confidence in confidences:
            if image_on_screen(image_name, confidence=confidence):
                return image_name, confidence
    return None, None


def screen_has_any_image(image_names, confidences=(0.8, 0.7, 0.6)):
    """Return the first matching image name visible on screen, or None."""
    image_name, _confidence = find_matching_image(image_names, confidences)
    return image_name


POST_VERIFY_TIMEOUT = 60
POST_VERIFY_POLL_INTERVAL = 0.5
POST_VERIFY_FAILURE_CONFIDENCES = (0.85, 0.8, 0.75, 0.7, 0.65)
POST_VERIFY_SUCCESS_CONFIDENCES = (0.85, 0.8, 0.75, 0.7)

ANOTHER_ACCOUNT_IMAGES = (
    "already_verified_account.png",
    "we_found_another_account.png",
    "masked_account_email.png",
    "login_to_your_account.png",
    "reset_my_password.png",
)
UNABLE_TO_VERIFY_IMAGES = (
    "we_couldnt_verify_your_data1.png",
    "we_couldnt_verify_your_data.png",
)
SUCCESS_ONBOARDING_IMAGES = (
    "youre_in.png",
    "success.png",
    "continue.png",
    "continue1.png",
)


def detect_another_account_screen():
    """Detect duplicate-account screens from any distinctive UI element."""
    matched, confidence = find_matching_image(
        ANOTHER_ACCOUNT_IMAGES[:2],
        POST_VERIFY_FAILURE_CONFIDENCES,
    )
    if matched:
        return matched, confidence

    secondary_matches = []
    for image_name in ANOTHER_ACCOUNT_IMAGES[2:]:
        match, match_confidence = find_matching_image(
            (image_name,),
            POST_VERIFY_FAILURE_CONFIDENCES[:3],
        )
        if match:
            secondary_matches.append((match, match_confidence))

    if len(secondary_matches) >= 2:
        return secondary_matches[0][0], secondary_matches[0][1]

    return None, None


def detect_post_verify_outcome():
    """Classify the current screen after identity verification."""
    another_account_image, confidence = detect_another_account_screen()
    if another_account_image:
        print(
            f"Another account screen detected via {another_account_image} "
            f"(confidence={confidence})."
        )
        return RESULT_WE_FOUND_ANOTHER_ACCOUNT

    unable_to_verify_image, confidence = find_matching_image(
        UNABLE_TO_VERIFY_IMAGES,
        POST_VERIFY_FAILURE_CONFIDENCES,
    )
    if unable_to_verify_image:
        print(
            f"Unable to verify screen detected via {unable_to_verify_image} "
            f"(confidence={confidence})."
        )
        return RESULT_UNABLE_TO_VERIFY

    success_image, confidence = find_matching_image(
        SUCCESS_ONBOARDING_IMAGES,
        POST_VERIFY_SUCCESS_CONFIDENCES,
    )
    if success_image:
        print(
            f"Welcome onboarding screen detected via {success_image} "
            f"(confidence={confidence})."
        )
        return RESULT_CREATED

    return None


def wait_for_post_verify_outcome(timeout=POST_VERIFY_TIMEOUT):
    """Wait for a known post-verify outcome; failure screens take priority."""
    print(
        "Waiting for success, 'another account', or 'unable to verify' screen "
        f"(up to {timeout}s)..."
    )
    start_time = time.time()
    while time.time() - start_time < timeout:
        outcome = detect_post_verify_outcome()
        if outcome:
            return outcome
        time.sleep(POST_VERIFY_POLL_INTERVAL)
    return None


def format_signature(config):
    """Match FanDuel's expected first + last name casing in the signature field."""
    first = (config.get("firstName") or "").strip().title()
    last = (config.get("lastName") or "").strip().title()
    return f"{first} {last}"


def on_job_signature_page():
    return screen_has_any_image(
        ["verify_identity_button.png", "job_field.png"],
        confidences=(0.75, 0.65, 0.55),
    )


def scroll_job_signature_page(clicks=2, amount=-200):
    """Focus the join modal and scroll its content down."""
    human_click_coords(*JOB_MODAL_FOCUS_COORDS)
    time.sleep(0.3)
    for _ in range(clicks):
        check_stop()
        pyautogui.scroll(amount)
        time.sleep(0.3)


def click_info_correct_checkbox():
    """Always confirm the registration accuracy checkbox."""
    if human_click_image("info_correct_checkbox.png"):
        print("Info correct checkbox clicked via image.")
        return True

    if human_click_coords(*INFO_CORRECT_CHECKBOX_COORDS):
        print(f"Info correct checkbox clicked at {INFO_CORRECT_CHECKBOX_COORDS}.")
        return True

    print("Info correct checkbox click failed.")
    return False


def click_verify_identity_button():
    """Click the verify identity button by image or fixed coordinates."""
    if human_click_image("verify_identity_button.png"):
        print("Verify identity button clicked via image.")
        return True

    if human_click_coords(*VERIFY_IDENTITY_BUTTON_COORDS):
        print(f"Verify identity button clicked at {VERIFY_IDENTITY_BUTTON_COORDS}.")
        return True

    print("Verify identity button click failed.")
    return False


def complete_welcome_onboarding():
    """Finish account creation through welcome, terms, and payment pages via coordinates."""
    print("Starting welcome onboarding flow...")

    print("Welcome page: clicking focus point...")
    human_click_coords(*WELCOME_FOCUS_COORDS)
    time.sleep(1)

    print("Welcome page: scrolling down...")
    check_stop()
    pyautogui.scroll(WELCOME_SCROLL_AMOUNT)
    time.sleep(2)

    print("Welcome page: clicking continue...")
    human_click_coords(*WELCOME_CONTINUE_COORDS)
    time.sleep(5)

    print("Next page: scrolling down...")
    check_stop()
    pyautogui.scroll(ONBOARDING_SCROLL_AMOUNT)
    time.sleep(2)

    print("Next page: clicking continue...")
    human_click_coords(*ONBOARDING_CONTINUE_COORDS)
    time.sleep(5)

    print("Payment page: scrolling down...")
    check_stop()
    pyautogui.scroll(ONBOARDING_SCROLL_AMOUNT)
    time.sleep(2)

    print("Payment page: clicking continue...")
    human_click_coords(*ONBOARDING_CONTINUE_COORDS)
    time.sleep(5)

    print("Welcome onboarding flow complete.")


PROXY_USERNAME_COORDS = (557, 221)
PROXY_PASSWORD_COORDS = (563, 266)
PROXY_SIGN_IN_COORDS = (793, 333)
SIGNATURE_FIELD_COORDS = (510, 612)
INFO_CORRECT_CHECKBOX_COORDS = (510, 223)
VERIFY_IDENTITY_BUTTON_COORDS = (662, 410)
JOB_MODAL_FOCUS_COORDS = (683, 400)
WELCOME_FOCUS_COORDS = (512, 450)
WELCOME_CONTINUE_COORDS = (682, 340)
WELCOME_SCROLL_AMOUNT = -500
ONBOARDING_CONTINUE_COORDS = (665, 600)
ONBOARDING_SCROLL_AMOUNT = -200
PROXY_DIALOG_WAIT_SECONDS = 4
PROXY_DIALOG_DETECT_TIMEOUT = 5
PROXY_DIALOG_RETRY_TIMEOUT = 5
PROXY_DIALOG_POLL_CONFIDENCE = 0.75
PROXY_DIALOG_CLEAR_TIMEOUT = 5
PROXY_POST_AUTH_WAIT_SECONDS = 5
PROXY_AUTH_MAX_ATTEMPTS = 3


def proxy_dialog_on_screen(confidence=PROXY_DIALOG_POLL_CONFIDENCE):
    return image_on_screen("proxy_sign_in.png", confidence=confidence)


def wait_for_proxy_dialog(timeout=PROXY_DIALOG_DETECT_TIMEOUT, confidence=PROXY_DIALOG_POLL_CONFIDENCE):
    """Poll until the Edge proxy sign-in dialog header is visible."""
    print(f"Waiting up to {timeout}s for proxy dialog...")
    if wait_for_image("proxy_sign_in.png", timeout=timeout, confidence=confidence):
        print("Proxy dialog detected.")
        return True
    print("Proxy dialog not detected via image matching.")
    return False


def wait_for_proxy_dialog_cleared(timeout=PROXY_DIALOG_CLEAR_TIMEOUT, confidence=PROXY_DIALOG_POLL_CONFIDENCE):
    """Poll until the proxy sign-in dialog is no longer visible."""
    print(f"Waiting up to {timeout}s for proxy dialog to clear...")
    start = time.time()
    while time.time() - start < timeout:
        check_stop()
        if not proxy_dialog_on_screen(confidence):
            print("Proxy dialog cleared.")
            return True
        time.sleep(0.5)
    print("Proxy dialog still visible.")
    return False


def _fill_proxy_credentials(proxy):
    human_click_coords(*PROXY_USERNAME_COORDS)
    time.sleep(0.5)
    clear_and_type(proxy["user"], backspace_count=max(len(proxy["user"]), 20) + 10)

    check_stop()
    human_click_coords(*PROXY_PASSWORD_COORDS)
    time.sleep(0.5)
    clear_and_type(proxy["pass"], backspace_count=max(len(proxy["pass"]), 20) + 10)

    check_stop()
    human_click_coords(*PROXY_SIGN_IN_COORDS)


def authenticate_proxy(proxy, max_attempts=PROXY_AUTH_MAX_ATTEMPTS):
    """Fill Edge HTTP proxy credentials; wait for dialog before each attempt."""
    for attempt in range(1, max_attempts + 1):
        check_stop()
        print(f"Proxy authentication attempt {attempt}/{max_attempts}")

        if attempt == 1:
            dialog_visible = wait_for_proxy_dialog()
            if not dialog_visible:
                print(
                    f"Falling back to {PROXY_DIALOG_WAIT_SECONDS}s fixed wait before coordinate entry..."
                )
                time.sleep(PROXY_DIALOG_WAIT_SECONDS)
        else:
            if not wait_for_proxy_dialog(timeout=PROXY_DIALOG_RETRY_TIMEOUT):
                print("Proxy dialog no longer visible; authentication complete.")
                return
            print("Proxy dialog visible again; retrying credential entry.")

        _fill_proxy_credentials(proxy)
        print("Submitted proxy credentials.")
        time.sleep(PROXY_POST_AUTH_WAIT_SECONDS)

        if wait_for_proxy_dialog_cleared():
            print("Proxy authentication complete.")
            return

        if attempt < max_attempts:
            print("Proxy dialog still present; preparing another attempt...")

    print("Proxy authentication complete (exhausted attempts).")


# ------------------------------------------------------------
# MAIN AUTOMATION FLOW (using image recognition)
# ------------------------------------------------------------
def main(config, url, proxy=None):
    print(f"Starting FanDuel automation for: {config.get('email')}")
    check_stop()
    launch_chrome_with_proxy(url, proxy)

    if proxy:
        authenticate_proxy(proxy)
    else:
        print("No proxy provided. Waiting for page to load...")
        time.sleep(10)

    check_stop()
    print("Waiting for homepage to load...")
    time.sleep(30)
    # 1. Click Join button (image: join_button.png)
    if not human_click_image("join_button.png"):
        if not human_click_coords(1262, 148):
            raise AutomationError("Join button not found - image and coordinates both failed.")
    random_delay(15, 20)
    check_stop()
    time.sleep(25)
    # take_screenshot()

    # 2. Email field
    # Try image first, fallback to coordinates
    
    
    if not human_click_image("email1.png"):
        if not human_click_coords(519, 481):
            raise AutomationError("Email field not found - image and coordinates both failed.")
        time.sleep(5)

    # Type email (reached here means one of them worked)
    check_stop()
    time.sleep(5)
    human_type(config["email"])
    print(f"Typed email: {config['email']}")
    check_stop()
    time.sleep(5)

    # 3. Continue button
    if not human_click_coords(666, 542):
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
        if not human_click_coords(505, 591):
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
    if human_click_coords(505, 660):
        human_type(config["password"])
        print(f"Typed password: {config['password']}")
        check_stop()
        random_delay(6, 9)
        # take_screenshot()
    else:
        raise AutomationError("Password field not found.")

    for _ in range(10):
        if image_on_screen("create_account.png", confidence=0.8):
            print("Create Account button visible.")
            break
        pyautogui.scroll(-200)
        time.sleep(1)
    check_stop()
    time.sleep(1.5)

    # 6. Create Account button (submit)
    if not human_click_image("create_account.png"):
        if not human_click_coords(670, 470):
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
            
        time.sleep(3)

    if service_unavailable:
        print("Service not available page detected. Ending for this account.")
        take_result_screenshot(prefix="service_not_available")
        return False, RESULT_SERVICE_NOT_AVAILABLE
        
    random_delay(2, 4)
    time.sleep(3)

    # 7. Now on Name page – fill first name, last name
    for attempt in range(2):
        print(f"Name Page - Attempt {attempt + 1}")
        
        click_image_or_coord("firstname_field.png", 510, 470)
        clear_and_type(config["firstName"], len(config["firstName"]) + 10)
        print(f"Typed first name: {config['firstName']}")
        time.sleep(2)
        
        if config["middleName"]:
            click_image_or_coord("middlename_field.png", 510, 550)
            clear_and_type(config["middleName"], len(config["middleName"]) + 10)
            print(f"Typed middle name: {config['middleName']}")
            time.sleep(2)
            
        click_image_or_coord("lastname_field.png", 510, 640)
        clear_and_type(config["lastName"], len(config["lastName"]) + 10)
        print(f"Typed last name: {config['lastName']}")
        time.sleep(2)
        
        random_delay(2, 4)
        if not human_click_image("next_btn.png"):
            if not human_click_coords(670, 700):
                raise AutomationError("Next button not found.")

        print("Clicking verification window...")
        time.sleep(5)
        human_click_coords(670, 560)
            
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

        print("Scrolling down on DOB page...")
        check_stop()
        pyautogui.scroll(-200)
        time.sleep(5)

        # Month
        human_click_coords(540, 380)
        time.sleep(5)
        if attempt == 0:
            month_str = str(config["month"]).lower()
            # Convert "11" to "nov", "01" to "jan", etc. if it's numeric
            month_map = {"01":"jan","1":"jan","02":"feb","2":"feb","03":"mar","3":"mar","04":"apr","4":"apr","05":"may","5":"may","06":"jun","6":"jun","07":"jul","7":"jul","08":"aug","8":"aug","09":"sep","9":"sep","10":"oct","11":"nov","12":"dec"}
            short_month = month_map.get(month_str, month_str[:3])
            clear_and_type(short_month, 5)
            time.sleep(5)
        else:
            random_delay(3, 5)
            month_coords = {
                "01": (560, 394), "1": (560, 394), "january": (560, 394), "jan": (560, 394),
                "02": (560, 416), "2": (560, 416), "february": (560, 416), "feb": (560, 416),
                "03": (560, 438), "3": (560, 438), "march": (560, 438), "mar": (560, 438),
                "04": (560, 460), "4": (560, 460), "april": (560, 460), "apr": (560, 460),
                "05": (560, 482), "5": (560, 482), "may": (560, 482),
                "06": (560, 504), "6": (560, 504), "june": (560, 504), "jun": (560, 504),
                "07": (560, 526), "7": (560, 526), "july": (560, 526), "jul": (560, 526),
                "08": (560, 548), "8": (560, 548), "august": (560, 548), "aug": (560, 548),
                "09": (560, 570), "9": (560, 570), "september": (560, 570), "sep": (560, 570),
                "10": (560, 592), "october": (560, 592), "oct": (560, 592),
                "11": (560, 614), "november": (560, 614), "nov": (560, 614),
                "12": (560, 636), "december": (560, 636), "dec": (560, 636)
            }
            target_month = str(config["month"]).lower()
            if target_month in month_coords:
                mx, my = month_coords[target_month]
                human_click_coords(mx, my)
            time.sleep(5)

        # Day field
        click_image_or_coord("day_field.png", 650, 380)
        clear_and_type(config["day"], 5)
        print(f"Typed day: {config['day']}")
        time.sleep(2)
        
        # Year field
        click_image_or_coord("year_field.png", 770, 380)
        clear_and_type(config["year"], 6)
        print(f"Typed year: {config['year']}")
        time.sleep(2)
        
        # Phone field
        click_image_or_coord("phone_field.png", 510, 450)
        clear_and_type(config["phone"], 15)
        print(f"Typed phone: {config['phone']}")
        time.sleep(2)   
        
        if not human_click_image("next_btn.png"):
            if not human_click_coords(675, 570):
                raise AutomationError("Next button not found.")

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

        print("Scrolling down on Address page...")
        check_stop()
        pyautogui.scroll(-300)
        time.sleep(1)

        click_image_or_coord("address_field.png", 510, 300)
        clear_and_type(config["address"], len(config["address"]) + 10)
        print(f"Typed address line 1: {config['address']}")
        pyautogui.press("enter")
        time.sleep(5)

        click_image_or_coord("apt1.png", 510, 350)
        if not config.get("apt"):
            human_type("apt")
            time.sleep(0.5)
            for _ in range(3): pyautogui.press('backspace'); time.sleep(0.1)
        else:
            clear_and_type(config["apt"], len(config["apt"]) + 10)
        print(f"Typed address line 2: {config.get('apt') or '(empty)'}")
        time.sleep(2)

        human_click_coords(510, 430)
        clear_and_type(config["city"], len(config["city"]) + 10)
        print(f"Typed city: {config['city']}")
        time.sleep(2)

        human_click_coords(510, 520)
        clear_and_type(config["province"], len(config["province"]) + 10)
        print(f"Typed province: {config['province']}")
        time.sleep(2)

        human_click_coords(700, 520)
        clear_and_type(config["postcode"], len(config["postcode"]) + 10)
        print(f"Typed postal code: {config['postcode']}")
        time.sleep(1)
                
        random_delay(1.5, 2.5)
        if not human_click_image("next_btn.png"):
            if not human_click_coords(670, 610):
                raise AutomationError("Next button not found.")
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

        click_image_or_coord("job_field.png", 510, 531)
        time.sleep(1)
        if not human_click_image("unemployed_option.png"):
            print("Unemployed option image not found, falling back to coord.")
            if not human_click_coords(510, 550):
                raise AutomationError("Unemployed option not found.")

        human_click_coords(*SIGNATURE_FIELD_COORDS)
        time.sleep(1)
        signature_text = format_signature(config)
        clear_and_type(signature_text, backspace_count=40)
        print(f"Typed signature: {signature_text}")
        time.sleep(1)

        print("Removing focus from signature field before scrolling...")
        human_click_coords(683, 350)
        time.sleep(0.5)

        print("Scrolling down on Job Status page...")
        check_stop()
        scroll_job_signature_page(clicks=2, amount=-200)
        time.sleep(1)

        if not click_info_correct_checkbox():
            print("Checkbox click failed, retrying...")
            continue
        time.sleep(1)

        print("Scrolling to reveal Verify button...")
        scroll_job_signature_page(clicks=1, amount=-200)
        time.sleep(1)

        random_delay(1, 2)
        if not click_verify_identity_button():
            print("Verify my identity button not found, triggering retry...")
            continue

        print("Waiting for page to advance after verify...")
        time.sleep(15)
        if not on_job_signature_page():
            print("Left job/signature page after verify.")
            break
        print("Still on job/signature page after verify; retrying...")
    else:
        if on_job_signature_page():
            raise AutomationError("Stuck on job/signature page after verify.")
        print("Left job/signature page; continuing to welcome onboarding.")

    # --- FINAL VERIFICATION AND WELCOME ONBOARDING ---
    post_verify_outcome = wait_for_post_verify_outcome()

    if post_verify_outcome == RESULT_UNABLE_TO_VERIFY:
        print("'We couldn't verify your data' screen detected. Taking screenshot and ending.")
        take_result_screenshot(prefix="unable_to_verify")
        print("Automation finished for this account due to verification failure.")
        return False, RESULT_UNABLE_TO_VERIFY

    if post_verify_outcome == RESULT_WE_FOUND_ANOTHER_ACCOUNT:
        print("'We found another account' screen detected. Taking screenshot and ending.")
        take_result_screenshot(prefix="we_found_another_account")
        print("Automation finished for this account due to finding another account.")
        return False, RESULT_WE_FOUND_ANOTHER_ACCOUNT

    if post_verify_outcome != RESULT_CREATED:
        print(
            "No known post-verify screen detected after waiting. "
            "Taking screenshot and ending without creating account."
        )
        take_result_screenshot(prefix="post_verify_unknown")
        return False, RESULT_SUCCESS_NOT_CREATED

    print("Proceeding with welcome onboarding after job/signature page...")
    time.sleep(5)
    complete_welcome_onboarding()
    print("Automation finished for this account.")
    return True, RESULT_CREATED

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
