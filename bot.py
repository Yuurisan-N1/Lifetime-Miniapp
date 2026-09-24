import asyncio
import json
import os
import re
import signal
import sys
import time
import urllib.parse

import aiohttp

from utils.banner import show_banner

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"

MY_PROJECT = "Lifetime Energy"
BASE_URL   = "https://lifetime-energy-bot.ih0st.app"
REF_CODE   = "6004380466"

HEADERS_BASE = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "identity",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": BASE_URL,
    "pragma": "no-cache",
    "referer": f"{BASE_URL}/?tgWebAppStartParam={REF_CODE}",
    "sec-ch-ua": '"Chromium";v="134", "Not?A_Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
}


def log_green(msg):
    print(f"{GREEN}{BOLD}{msg}{RESET}", flush=True)


def log_yellow(msg):
    print(f"{YELLOW}{BOLD}{msg}{RESET}", flush=True)


def log_red(msg):
    print(f"{RED}{BOLD}{msg}{RESET}", flush=True)


def signal_handler(sig, frame):
    print()
    log_red("Script stopped by user")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def clean_text(value, fallback):
    text = str(value)
    for symbol in "[]|#!@$%^&*()-":
        text = text.replace(symbol, " ")
    text = " ".join(text.split())
    return text if text else fallback


def clean_text_num(value, digits=6):
    try:
        number = float(value)
    except Exception:
        number = 0.0
    if number and abs(number) < 0.001:
        body, power = ("%.3e" % number).split("e")
        return "%se%d" % (body, int(power))
    return "%.*f" % (digits, number)


def normalize_proxy(line):
    line = str(line).strip()
    if "://" in line:
        return line
    parts = line.split(":")
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    if len(parts) == 3:
        return f"http://{parts[2]}@{parts[0]}:{parts[1]}"
    if len(parts) >= 4:
        return f"http://{parts[2]}:{':'.join(parts[3:])}@{parts[0]}:{parts[1]}"
    return line


def mask_proxy(proxy_url):
    try:
        after_scheme = str(proxy_url).split("://")[-1]
        after_at = after_scheme.split("@")[-1]
        ip_part = after_at.split(":")[0]
        port_part = after_at.split(":")[1] if ":" in after_at else ""
        octets = ip_part.split(".")
        if len(octets) == 4:
            masked_ip = f"{octets[0]}*****{octets[3]}"
            return f"http://user:pass@{masked_ip}:{port_part}"
        if len(ip_part) > 4:
            masked_ip = f"{ip_part[:2]}*****{ip_part[-2:]}"
            return f"http://user:pass@{masked_ip}:{port_part}"
    except Exception:
        pass
    return "http://user:pass@***:***"


def mask_secrets(text):
    text = re.sub(r"(://)[^\s/@]+:[^\s/@]+", r"\1***", str(text))
    text = re.sub(r"user:pass", "***", text)
    return re.sub(r"(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})", r"\1*****\4", text)


def format_duration(seconds):
    seconds = max(0, int(seconds))
    return "%02d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


def countdown(seconds, label):
    for remaining in range(max(0, int(seconds)), 0, -1):
        sys.stdout.write(f"\r{YELLOW}{BOLD}{label} {format_duration(remaining)}{RESET}")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write(f"\r{YELLOW}{BOLD}{label} {format_duration(0)}{RESET}")
    sys.stdout.flush()
    print()


def load_config():
    defaults = {"settings": {"sleep_seconds": 14400}}
    if not os.path.exists("config.json"):
        return defaults
    try:
        with open("config.json") as handle:
            return json.load(handle)
    except Exception:
        return defaults


def load_data():
    if not os.path.exists("data.txt"):
        log_red("File data.txt was not found")
        sys.exit(1)
    lines = [line.strip().split("|")[0].strip()
             for line in open("data.txt").readlines() if line.strip()]
    if not lines:
        log_red("File data.txt is empty")
        sys.exit(1)
    return lines


def load_proxies():
    if not os.path.exists("proxy.txt"):
        return []
    try:
        return [line.strip() for line in open("proxy.txt").readlines() if line.strip()]
    except Exception:
        return []


def get_proxy(proxies, idx):
    if not proxies:
        return None
    return normalize_proxy(proxies[idx % len(proxies)])


def account_label(init_data):
    try:
        user = json.loads(urllib.parse.parse_qs(init_data).get("user", ["{}"])[0])
        name = user.get("username") or user.get("first_name") or "Unknown"
        return clean_text(name, "account")
    except Exception:
        return "account"


def cooldown_left(stamp_ms):
    try:
        left = int(stamp_ms) / 1000.0 - time.time()
    except Exception:
        return 0
    return max(0, int(left))


def banner():
    try:
        show_banner(MY_PROJECT)
    except Exception:
        pass


async def post(session, endpoint, init_data, proxy=None, extra=None, query=False):
    url = f"{BASE_URL}/miniapp{endpoint}"
    try:
        if query:
            target = f"{url}?tid=5&initData={urllib.parse.quote(init_data)}"
            async with session.get(target, proxy=proxy) as resp:
                raw = await resp.read()
                status = resp.status
        else:
            payload = {"initData": init_data, "tid": 5}
            if extra:
                payload.update(extra)
            async with session.post(f"{url}?tid=5", json=payload, proxy=proxy) as resp:
                raw = await resp.read()
                status = resp.status
    except Exception as exc:
        log_red(f"Request to {clean_text(endpoint, 'request')} failed with "
                f"{clean_text(mask_secrets(type(exc).__name__), 'error')}")
        return None
    if status != 200:
        log_red(f"Request to {clean_text(endpoint, 'request')} answered with "
                f"HTTP {clean_text(status, 0)}")
        return None
    try:
        return json.loads(raw)
    except Exception:
        log_red(f"Request to {clean_text(endpoint, 'request')} answered with an unreadable body")
        return None


async def phase_auth(session, init_data, proxy, label):
    data = await post(session, "/auth", init_data, proxy)
    if not data or not data.get("ok"):
        log_red(f"Account {clean_text(label, 'account')} failed to log in with "
                f"{clean_text((data or {}).get('error'), 'no reason')}")
        return {}
    user = data.get("user") or {}
    log_green(f"Account {clean_text(label, 'account')} logged in")
    log_green(f"Balance holds {clean_text(user.get('power'), 0)} WATTS and "
              f"{clean_text_num(user.get('hashes'))} ENERGY with "
              f"{clean_text(user.get('valid_refs'), 0)} valid referrals")
    return user


async def phase_welcome(session, init_data, proxy, label, user):
    if user.get("welcome_bonus_claimed"):
        log_green("Welcome bonus was already credited on this account")
        return 0
    data = await post(session, "/claim-welcome-bonus", init_data, proxy)
    if data and data.get("ok"):
        log_green(f"Welcome bonus credited {clean_text(data.get('power_awarded'), 0)} "
                  f"WATTS of permanent power")
        return int(data.get("power_awarded") or 0)
    log_yellow(f"Welcome bonus was refused with "
               f"{clean_text((data or {}).get('error'), 'no reason')}")
    return 0


async def phase_production(session, init_data, proxy, label):
    data = await post(session, "/start-production", init_data, proxy)
    if not data:
        return
    if not data.get("ok"):
        log_yellow(f"Production session was refused with "
                   f"{clean_text(data.get('error'), 'no reason')}")
        return
    if clean_text(data.get("message"), "") == "session already active":
        left = cooldown_left((data.get("ends_at") or 0) * 1000)
        log_yellow(f"Production session is still running with {format_duration(left)} left")
        return
    log_green(f"Production session started for {clean_text(data.get('session_hours'), 0)} hours "
              f"with {clean_text_num(data.get('total_hashes'))} ENERGY queued")


async def phase_claim(session, init_data, proxy, label):
    data = await post(session, "/claim", init_data, proxy)
    if not data:
        return 0
    if not data.get("ok"):
        log_yellow(f"Hash claim was refused with {clean_text(data.get('error'), 'no reason')}")
        return 0
    log_green(f"Hash claim added {clean_text_num(data.get('hashes_added'))} ENERGY for a total of "
              f"{clean_text_num(data.get('total_hashes'))} ENERGY worth "
              f"{clean_text_num(data.get('total_hashes_ton'), 8)} TON")
    return float(data.get("total_hashes") or 0)


async def phase_ad(session, init_data, proxy, title, endpoint):
    data = await post(session, endpoint, init_data, proxy)
    if not data:
        return False
    if data.get("ok"):
        log_green(f"{clean_text(title, 'Ad task')} rolled face {clean_text(data.get('face'), 0)} "
                  f"and credited {clean_text(data.get('pips_awarded'), 0)} WATTS")
        return True
    if data.get("error") == "cooldown":
        left = cooldown_left(data.get("next_claim_at"))
        log_yellow(f"{clean_text(title, 'Ad task')} is on cooldown for {format_duration(left)}")
        return False
    log_yellow(f"{clean_text(title, 'Ad task')} was refused with "
               f"{clean_text(data.get('error'), 'no reason')}")
    return False


async def phase_slot(session, init_data, proxy):
    data = await post(session, "/tasks/slot-spin", init_data, proxy)
    if not data:
        return False
    if data.get("ok"):
        log_green(f"Slot spin credited {clean_text(data.get('pips_awarded'), 0)} WATTS "
                  f"from the reels the server picked")
        return True
    if data.get("error") == "cooldown":
        left = cooldown_left(data.get("next_spin_at"))
        log_yellow(f"Slot spin is on cooldown for {format_duration(left)}")
        return False
    log_yellow(f"Slot spin was refused with {clean_text(data.get('error'), 'no reason')}")
    return False


async def phase_tasks(session, init_data, proxy, label):
    data = await post(session, "/tasks", init_data, proxy, query=True)
    if not data or not data.get("ok"):
        log_yellow("Task list was refused by the server")
        return 0
    tasks = data.get("tasks") or []
    done = 0
    locked = 0
    for task in tasks:
        if task.get("completed") or task.get("type") in ("ad", "ad2"):
            continue
        if not task.get("eligible", True):
            locked += 1
            continue
        task_id = task.get("id")
        title = task.get("labelEn") or task_id
        await post(session, "/tasks/start", init_data, proxy, extra={"task_id": task_id})
        res = await post(session, "/tasks/claim", init_data, proxy, extra={"task_id": task_id})
        if res and res.get("ok"):
            done += 1
            log_green(f"Task {clean_text(title, 'task')} credited "
                      f"{clean_text(res.get('pips_awarded'), 0)} WATTS")
        else:
            log_yellow(f"Task {clean_text(title, 'task')} was refused with "
                       f"{clean_text((res or {}).get('error'), 'no reason')}")
    if done:
        log_green(f"All available tasks were claimed for {clean_text(done, 0)} rewards")
    elif locked:
        log_yellow(f"{clean_text(locked, 0)} tasks stay locked until their invites land")
    else:
        log_green(f"Every available task was already claimed with "
                  f"{clean_text(data.get('referral_count'), 0)} referrals")
    return done


async def run_account(init_data, proxy):
    label = account_label(init_data)
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(headers=HEADERS_BASE, timeout=timeout) as session:
            user = await phase_auth(session, init_data, proxy, label)
            if not user:
                return
            await phase_welcome(session, init_data, proxy, label, user)
            await phase_production(session, init_data, proxy, label)
            await phase_claim(session, init_data, proxy, label)
            await phase_ad(session, init_data, proxy, "Daily dice", "/tasks/ad-roll")
            await phase_ad(session, init_data, proxy, "Six hour dice", "/tasks/ad-roll2")
            await phase_slot(session, init_data, proxy)
            await phase_tasks(session, init_data, proxy, label)
            total = await phase_claim(session, init_data, proxy, label)
            log_green(f"Cycle closed with {clean_text_num(total)} ENERGY in production")
    except Exception as exc:
        log_red(f"Account {clean_text(label, 'account')} failed with "
                f"{clean_text(mask_secrets(type(exc).__name__), 'error')}")


async def main_async(accounts, proxies, sleep_secs):
    cycle = 1
    while True:
        log_yellow(f"Starting automation cycle number {clean_text(cycle, 1)}")

        for idx, init_data in enumerate(accounts):
            if idx > 0:
                print()

            proxy_url = get_proxy(proxies, idx)
            if proxy_url:
                log_yellow(f"Using proxy {mask_proxy(proxy_url)}")

            await run_account(init_data, proxy_url)

        log_yellow(f"Automation cycle number {clean_text(cycle, 1)} is complete")
        cycle += 1
        countdown(sleep_secs, "Next cycle starts in")
        banner()


def main():
    banner()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    config = load_config()
    sleep_secs = int(config.get("settings", {}).get("sleep_seconds", 14400))
    accounts = load_data()
    proxies = load_proxies()

    asyncio.run(main_async(accounts, proxies, sleep_secs))


if __name__ == "__main__":
    main()
