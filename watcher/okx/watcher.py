import httpx
import requests
from decimal import Decimal

from okx import Account, Trade

from config import TESTNET
from config.ws_server import URL_UPDATE_PROFILE

from watcher.base_watcher import BaseWatcher
from watcher.exceptions import AccountCanNotTrade
from watcher.okx.constants import FUTURES, MARKET, OrderSide, USDT
from watcher.utils import repeat_if_raised_exception


class OKXWatcher(BaseWatcher):
    exchange_name = 'OKX'

    api_key: str
    secret_key: str
    passphrase: str

    def __init__(self, *args, api_key: str, secret_key: str, passphrase: str, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

        self.account_api_client = Account.AccountAPI(
            api_key, secret_key, passphrase, flag=str(int(TESTNET)), debug=False
        )
        self.trade_api_client = Trade.TradeAPI(
            api_key, secret_key, passphrase, flag=str(int(TESTNET)), debug=False
        )

        self._force_http1(self.account_api_client)
        self._force_http1(self.trade_api_client)

        super().__init__(*args, **kwargs)

    @staticmethod
    def _force_http1(api):
        try:
            old = getattr(api, "client", None)
            base_url = getattr(old, "base_url", None)
            headers = getattr(old, "headers", None)
            timeout = getattr(old, "timeout", None)
            if old:
                try:
                    old.close()
                except Exception:
                    pass
            api.client = httpx.Client(http2=False, base_url=base_url, headers=headers, timeout=timeout)
        except Exception as e:
            print(f"[WARN] OKXWatcher: failed to force http1: {e}")

    @repeat_if_raised_exception(httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPError)
    def get_positions(self):
        r = self.account_api_client.get_positions(instType=FUTURES)
        return r.get("data", [])

    @repeat_if_raised_exception(httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPError)
    def get_balance(self):
        r = self.account_api_client.get_account_balance()
        data = r.get("data") or []
        details = data[0].get("details") if data else []
        return details or []

    def place_orders(self, orders: list):
        print('NEW ORDER!!!!!!')
        return self.trade_api_client.place_multiple_orders(orders)

    def update_balance_(self):
        balances = self.get_balance()
        print("[DEBUG] OKX balances:", balances)

        self.available_balance = Decimal("0")
        self.balance = Decimal("0")
        self.un_pnl = Decimal("0")

        for b in balances:
            try:
                if b.get("ccy") == USDT:
                    self.available_balance = Decimal(b.get("availBal", "0"))
                    self.balance = Decimal(b.get("cashBal", "0"))
                    self.un_pnl = Decimal(b.get("upl", "0"))
                    break
            except Exception as e:
                print(f"[WARN] parse balance row failed: {e}")

        print("[DEBUG] After update:", self.available_balance, self.balance, self.un_pnl)

        payload = {
                "id": self.id,
                "available_balance": str(self.available_balance),
                "balance": str(self.balance),
                "pnl": str(self.un_pnl),
                "max_balance": str(self.max_balance),
                "lose_streak": self.lose_streak,
                "trade_now": self.is_trade_now,
                "blocked": self.is_blocked,
            }
        try:
            requests.post(URL_UPDATE_PROFILE, json=payload, timeout=5)
        except Exception as e:
            print("sync error:", e)


    def close_trades(self):
        if not self.is_trade_now:
            return

        positions = self.get_positions()
        orders_to_place = []
        symbols = set()

        for p in positions:
            try:
                size = int(p["pos"])
                if size == 0:
                    continue
                inst_id = p["instId"]
                symbols.add(inst_id)
                orders_to_place.append({
                    "instId": inst_id,
                    "tdMode": p.get("mgnMode", "cross"),
                    "side": OrderSide.BUY if size < 0 else OrderSide.SELL,
                    "ordType": MARKET,
                    "posSide": p.get("posSide", "net"),
                    "sz": abs(size),
                })
            except Exception as e:
                print(f"[WARN] bad position row: {e}")

            if orders_to_place:
                print(self.place_orders(orders_to_place))
                self.send_message(f"Positions {symbols} closed!")