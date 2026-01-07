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

## Commands from client (UI)

### **Update profiles**
- **UI sends:** `update`
- **Server reloads** profiles from Django and replies: `{ "type": "ok", "cmd": "update" }`

### **Subscribe to live stream**
- **UI sends** a string with IDs separated by dots: `1.4.5`
- *(or a single id: `"3"`)*
- **Server starts streaming** updates for these IDs.

### **Streaming payload (server -> UI)**
- **Server sends** JSON array of rows (**only changed rows**):
```json
[
  [5, "98.0", "100.0", "100.0", "-2.0", true, false, 3],
  [9, "120.5", "125.0", "120.5", "0.5", false, true, 0]
]

