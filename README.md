<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=Lifetime%20Energy%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=Auto%20Production%20%7C%20Hash%20Claims%20%7C%20Dice%20%7C%20Slot%20%7C%20Tasks%20%7C%20Auto%20Withdraw&descAlign=50&descAlignY=58"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Auto+Start+Production+Session+%7C+Hash+Claim;Auto+Welcome+Bonus+%7C+Permanent+Power;Auto+Daily+Dice+%7C+Six+Hour+Dice+%7C+Slot+Spin;Auto+Task+Claims+%7C+Referral+Progress;Auto+Swap+To+TON+%7C+Proxy+Support+%7C+Multi-Account"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white"/>
  <img alt="platform" src="https://img.shields.io/badge/Platform-Lifetime%20Energy%20Miniapp-111111"/>
  <img alt="multi-account" src="https://img.shields.io/badge/Multi--Account-Supported-111111"/>
  <img alt="proxy" src="https://img.shields.io/badge/Proxy-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>Lifetime Energy Bot</b> is a full automation bot for the Lifetime Energy Telegram Miniapp.<br/>
  It handles the complete cycle: claiming the welcome power, opening the production session, syncing the energy the server has produced, rolling the daily dice, the six hour dice and the slot, claiming every open task, and swapping the balance to TON once the minimum is met, all running automatically across multiple accounts with an account-bound proxy, a per-account device profile and a live countdown between cycles.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Features](#features)
- [File Structure](#file-structure)
- [Disclaimer](#disclaimer)

---

## Requirements

- Python `3.12+`
- Git

---

## Installation

**Clone the repository:**

```bash
git clone https://github.com/Yuurisan-N1/LifetimeMiniapp.git
cd Lifetime-Miniapp
```

**Install dependencies:**

```bash
pip install aiohttp yuurisan
```

---

## Configuration

### 1. Accounts (data.txt)

Fill `data.txt` with Telegram WebApp `initData` for each account, one per line. A wallet address for the swap can be appended after a pipe:

```
user=%7B%22id%22...&hash=abc123
user=%7B%22id%22...&hash=def456|UQ...wallet
```

> `initData` can be obtained from the browser DevTools when opening Lifetime Energy on Telegram Web.

### 2. Proxy (proxy.txt)

Fill `proxy.txt` with proxies, one per line:

```
host:port
host:port:user:pass
http://user:pass@host:port
```

The first unassigned line in the pool is bound to the account that needs one and is then removed from the file, so an account keeps the same exit IP on every later cycle. The binding is stored in `proxy.json` keyed by the account user ID. An account without a bound proxy is skipped, so two accounts never share one exit IP.

### 3. Bot Settings (config.json)

`sleep_seconds` controls how many seconds the bot waits between cycles. If `config.json` is missing, it is created automatically with a default of `3600` seconds.

---

## Running the Bot

```bash
python bot.py
```

Press `Ctrl+C` at any time to stop the bot cleanly.

---

## Features

### Auto Auth
Authenticates every account with its own `initData` and logs the permanent power, the energy currently held and the number of valid referrals straight from the server response.

### Auto Welcome Bonus
Claims the one-time welcome power when the account has not claimed it yet, and reports that it was already credited on every later run.

### Auto Production
Opens the production session that converts permanent power into energy. The session length comes from the server, and a session that is still running is reported with the exact time left instead of being restarted.

### Auto Hash Claim
Syncs the energy the server has produced so far and logs the amount added, the new total and the TON value of that total.

### Auto Dice and Slot
Rolls the daily dice, the six hour dice and the slot. Each reward comes from the server roll, and a task that is still cooling down is logged with the remaining time instead of being retried in a loop.

### Auto Tasks
Reads the task list and finishes every open entry by anchoring it with the server first and then claiming it, so a bot task is credited to the account that actually opened it. Tasks the server refuses are reported with the reason it returned.

### Auto Withdraw
Reads the swap minimum and the energy balance from the server; when the balance reaches the minimum and a wallet address is present in `data.txt`, the swap is submitted with that address.

### Multi Account
All accounts in `data.txt` are processed sequentially within every cycle, one at a time, so an account never shares an exit IP with another. The account name, its power balance and its referral count are logged at the start of each account.

### Proxy Support
The proxy pool is loaded from `proxy.txt` and each account binds its own line permanently; the bound line is then dropped from the pool so no two accounts ever share one exit IP. The binding is kept in `proxy.json` keyed by the account user ID, which is created on the first run and is not part of this archive. Proxy credentials and exit IPs are masked in log output. An account that cannot be given a proxy is skipped instead of running on the local IP.

### Auto Countdown
After all accounts complete a cycle, the bot displays a live countdown until the next cycle starts.

---

## File Structure

```text
LifetimeEnergy-Miniapp/
├── bot.py          # Main bot, full cycle automation
├── config.json     # Sleep duration between cycles
├── data.txt        # Account initData, one per line
├── proxy.txt       # Proxy list, one per line (optional)
├── LICENSE         # License file
└── utils/
    └── banner.py   # Banner using yuurisan module
```

---

## Disclaimer

This tool is built for educational and technical exploration purposes. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>
