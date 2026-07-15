import time


HOMEPAGE_URL = "https://ab.sportsbook.fanduel.ca/"
PROXY_COOLDOWN_SECONDS = 600


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
    proxy, wait_time = select_proxy(settings, now)
    return HOMEPAGE_URL, proxy, wait_time
