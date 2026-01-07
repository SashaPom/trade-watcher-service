Python Trade Watcher Service

A standalone Python service that runs **watchers** for a specific exchange (OKX or Binance), monitors account balance/positions, enforces risk limits, and streams live status to the UI via **WebSocket**.

This service is the **runtime/agent** part of the Risk Manager system.

---

## What this service does

### Core responsibilities
- Runs one process per exchange (`EXCHANGE_NAME=OKX` or `BINANCE`)
- Loads active profiles from the Django Manager service
- Creates a watcher thread per profile (one account = one watcher)
- Every ~1s:
  - updates balance / PnL from exchange API
  - checks risk limits (percent drawdown, amount drawdown, lose streak)
  - if limit hit → blocks profile + closes positions + sends Telegram notification
- Provides a WebSocket server for UI:
  - UI subscribes to profile IDs
  - service streams live updates only when values change

---

## How it fits into the platform

- **Django service (manager)** stores profiles, assigns them to a watcher server, and sends `"update"` over WS when profiles change.
- **This watcher service**:
  1) fetches assigned profiles from Django
  2) starts/stops watcher threads
  3) streams live state to the UI over WebSocket

---

## WebSocket protocol (UI <-> Watcher)

### On connect
   Server sends:
   ```json
   { "type": "hello" }
   ```

---

## Commands from client (UI)

1) Update profiles
   - UI sends:
   ```json
   update
   ```
   - Server reloads profiles from Django and replies:
  ```json
  { "type": "ok", "cmd": "update" }
  ```
2) Subscribe to live stream

  - UI sends a string with IDs separated by dots:
  ```json
  1.4.5
  ```
Server starts streaming updates for these IDs.

---

## Streaming payload (server -> UI)

Server sends JSON array of rows (only changed rows):
```json
[
  [5, "98.0", "100.0", "100.0", "-2.0", true, false, 3],
  [9, "120.5", "125.0", "120.5", "0.5", false, true, 0]
]
```

Row format:
1) id
2) balance
3) max_balance
4) available_balance
5) pnl
6) is_blocked
7) is_trade_now
8) lose_streak

If an ID is no longer active, watcher returns a “zero” row.

---

## Exchange selection

The same codebase supports multiple exchanges.
Set:

- EXCHANGE_NAME=OKX to run OKX watchers
- EXCHANGE_NAME=BINANCE to run Binance watchers

Internally, this switches Manager/Watcher implementation (OKXManager/OKXWatcher, etc.).

---

## Project structure

- **main.py** — entrypoint: starts WS server + initial profiles sync
- **ws.py** — lightweight wrapper around websockets.serve
- **handler.py**
    - handler_watcher() — WS handler
    - _stream_watchers() — async loop streaming live changes
    - update_profiles() — sync profiles from Django (runs in thread)
- watcher/
    - **base_watcher.py** — base threaded watcher with risk logic
    - **base_manager.py** — manager for active watchers (create/start/stop/update)
    - okx/ and binance/ — exchange-specific watchers/managers
    - exceptions.py — DuplicateWatcher, StopWatcher, etc.
    - **utils.py** — decorators, retries, mapping profile -> kwargs
    - **tg_bot.py** — Telegram notifications (send_message, optional polling)

---

## Risk logic (high level)

### Each profile watcher tracks:

- current balance and available_balance
- max_balance (peak since last reset)
- un_pnl / pnl
- lose_streak (series of negative updates)
- is_blocked flag

### Limits:

- **Percent drawdown**: block if (balance + pnl) drops by X% from max_balance
- **Amount drawdown**: block if drop from max_balance exceeds fixed amount
- **Lose streak**: block if losing updates >= limit

### When blocked:

- watcher attempts to close all positions (market close)
- continues monitoring but keeps profile blocked
- sends Telegram notification (if chat_id is configured)

### Daily reset:

- at configured clear_checking_time watcher can reset streak/max and unlock (depending on implementation)

---

## Configuration

### Environment variables (example)

- EXCHANGE_NAME — OKX or BINANCE

- WS_HOST — usually 0.0.0.0

- WS_PORT — e.g. 8889 (OKX), 8890 (Binance)

- DJANGO_API_URL — Django manager endpoint for profiles

- example: http://gateway:8080/api/py/dj/tw/api/watcher/profiles/

- ADDR (optional) — watcher identity header value (host:port)
    - used by Django to return profiles assigned to this watcher server

- TELEGRAM_BOT_TOKEN — for notifications

- SSL_CERT_PATH, SSL_KEY_PATH (optional) — enable WSS

**Important**: This service expects to reach Django via HTTP and be reachable by UI via WS (often through gateway proxy).

---

## Running locally
### 1) Install

```json
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start OKX watcher
```json
export EXCHANGE_NAME=OKX
export WS_HOST=0.0.0.0
export WS_PORT=8889
export DJANGO_API_URL=http://localhost:8000/api/watcher/profiles/
python main.py
```

### 3) Start Binance watcher (separate process)
```json
export EXCHANGE_NAME=BINANCE
export WS_PORT=8890
python main.py
```
