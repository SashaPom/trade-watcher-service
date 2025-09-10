from decimal import Decimal

from okx import Account, Trade

from config import TESTNET
from config.ws_server import URL_UPDATE_PROFILE

from watcher.base_watcher import BaseWatcher
from watcher.exceptions import AccountCanNotTrade
from watcher.okx.constants import FUTURES, MARKET, OrderSide, USDT


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

        super().__init__(*args, **kwargs)

    def get_positions(self):
        return self.account_api_client.get_positions(instType=FUTURES)['data']

    def get_balance(self):
        return self.account_api_client.get_account_balance()['data']

    def place_orders(self, orders: list):
        print('NEW ORDER!!!!!!')
        return self.trade_api_client.place_multiple_orders(orders)

    def update_balance_(self):
        balances = self.get_balance()
        print("[DEBUG] OKX balances:", balances)
        for balance in balances:
            if balance['ccy'] == USDT:
                self.available_balance = Decimal(balance['availBal'])
                self.balance = Decimal(balance['cashBal'])
                self.un_pnl = Decimal(balance['upl'])
            self.send_message("UPDATE_PROFILE")

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
            request_to_main(URL_UPDATE_PROFILE, method="POST", json=payload)
        except Exception as e:
            print("sync error:", e)


    def close_trades(self):
        if self.is_trade_now:
            positions = self.get_positions()
            orders_to_place = []
            symbols = set()

            for position in positions:
                size = int(position['pos'])
                inst_id = position['instId']

                symbols.add(inst_id)

                orders_to_place.append({
                    'instId': inst_id,
                    'tdMode': position['mgnMode'],
                    'side': OrderSide.BUY if size < 0 else OrderSide.SELL,
                    'ordType': MARKET,
                    'posSide': position['posSide'],
                    'sz': abs(size)
                })

            if orders_to_place:
                print(self.place_orders(orders_to_place))
                self.send_message(f'Positions {symbols} closed!')

    # def run_before(self):
    #     account_data = self.get_account_data()
    #     if not account_data['canTrade']:
    #         raise AccountCanNotTrade
