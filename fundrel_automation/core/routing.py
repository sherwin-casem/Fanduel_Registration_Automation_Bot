import random
import time


DEFAULT_REFERRAL_URL = "https://fndl.co/ohhanft"
PROXY_COOLDOWN_SECONDS = 600


def select_referral_url(settings, account_config=None, now=None):
    account_config = account_config or {}
    now = time.time() if now is None else now

    referrals = settings.get("referrals", [])
    enabled_referrals = [referral for referral in referrals if referral.get("enabled", True)]
    mode = settings.get("referral_mode", "rotate")
    state = settings.get("referral_state", {"index": 0, "start_time": 0, "random_bag": []})

    specific_url = account_config.get("referral_url")
    if specific_url and specific_url.strip():
        settings["referral_state"] = state
        return specific_url.strip()

    url = DEFAULT_REFERRAL_URL
    if not enabled_referrals:
        settings["referral_state"] = state
        return url

    if mode == "rotate":
        state["index"] = state.get("index", 0) % len(enabled_referrals)
        url = enabled_referrals[state["index"]]["url"]
        state["index"] = (state["index"] + 1) % len(enabled_referrals)

    elif mode == "sequential_60m":
        start_time = state.get("start_time", 0)
        if now - start_time >= 3600:
            state["index"] = (state.get("index", 0) + 1) % len(enabled_referrals)
            state["start_time"] = now
        elif start_time == 0:
            state["start_time"] = now

        state["index"] = state.get("index", 0) % len(enabled_referrals)
        url = enabled_referrals[state["index"]]["url"]

    elif mode == "random_mix":
        enabled_urls = [referral["url"] for referral in enabled_referrals]
        bag = [url for url in state.get("random_bag", []) if url in enabled_urls]
        if not bag:
            bag = enabled_urls[:]
            random.shuffle(bag)
        url = bag.pop(0)
        state["random_bag"] = bag

    elif mode == "percentage_allocation":
        weights = [referral.get("percentage", 100) for referral in enabled_referrals]
        total_weight = sum(weights)
        if total_weight <= 0:
            url = random.choice(enabled_referrals)["url"]
        else:
            rand_val = random.uniform(0, total_weight)
            cumulative = 0
            for referral, weight in zip(enabled_referrals, weights):
                cumulative += weight
                if rand_val <= cumulative:
                    url = referral["url"]
                    break
    else:
        url = enabled_referrals[0]["url"]

    settings["referral_state"] = state
    return url


def select_proxy(settings, now=None, cooldown=PROXY_COOLDOWN_SECONDS):
    now = time.time() if now is None else now
    proxies = settings.get("proxies", [])
    if not proxies:
        return None, 0

    unused_proxies = [proxy for proxy in proxies if proxy.get("last_use", 0) == 0]
    if unused_proxies:
        best_proxy = unused_proxies[0]
        min_wait = 0
    else:
        best_proxy = None
        min_wait = float("inf")

        for proxy in proxies:
            last_use = proxy.get("last_use", 0)
            wait_time = max(0, cooldown - (now - last_use))

            if wait_time == 0:
                best_proxy = proxy
                min_wait = 0
                break

            if wait_time < min_wait:
                min_wait = wait_time
                best_proxy = proxy

    best_proxy["last_use"] = now + min_wait
    return best_proxy, min_wait


def select_url_and_proxy(settings, account_config=None, now=None):
    url = select_referral_url(settings, account_config, now)
    proxy, wait_time = select_proxy(settings, now)
    return url, proxy, wait_time
