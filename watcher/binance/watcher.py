from decimal import Decimal

from binance.error import ClientError, ServerError
from binance.um_futures import UMFutures

from config import binance, TESTNET
from watcher.base_watcher import BaseWatcher
from watcher.binance.constants import MARKET, USDT, OrderSide
from watcher.binance.utils import limit_usage_from_response
from watcher.exceptions import AccountCanNotTrade
from watcher.utils import repeat_if_raised_exception


class BinanceWatcher(BaseWatcher):
    exchange_name = 'Binance'

    api_key: str
    secret_key: str
    limit_usage = {limit: 0 for limit in binance.LIMIT_NAMES}

    def __init__(self, *args, api_key: str, secret_key: str, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key

        self.client = UMFutures(
            api_key,
            secret_key,
            show_limit_usage=True,
            **({'base_url': binance.TESTNET_ADDRESS} if TESTNET else {}),
        )

        super().__init__(*args, **kwargs)

    @repeat_if_raised_exception(ClientError, ServerError)
    @limit_usage_from_response(binance.LIMIT_WEIGHT_60_NAME)
    def get_account_data(self):
        return self.client.account()

    @repeat_if_raised_exception(ClientError, ServerError)
    @limit_usage_from_response(binance.LIMIT_WEIGHT_60_NAME)
    def get_balance(self):
        return self.client.balance()

    @repeat_if_raised_exception(ClientError, ServerError)
    @limit_usage_from_response(binance.LIMIT_ORDERS_10_NAME, binance.LIMIT_ORDERS_60_NAME)
    def new_order(self, symbol: str, side: str, qty: str):
        return self.client.new_order(symbol, side, MARKET, quantity=qty)

    def update_balance_(self):
        for balance in self.get_balance():
            if balance['asset'] == USDT:
                self.available_balance = Decimal(balance['availableBalance'])
                self.balance = Decimal(balance['balance'])
                self.un_pnl = Decimal(balance['crossUnPnl'])

    def close_trade(self, symbol: str, qty: str):
        print('NEW ORDER!!!!!!', qty)
        if qty.startswith('-'):
            side = OrderSide.BUY
            qty = qty.replace('-', '')
        else:
            side = OrderSide.SELL

        self.new_order(symbol, side, qty)
        self.send_message(f'Position {symbol} closed!')

    def close_trades(self):
        if self.is_trade_now:
            account_data = self.get_account_data()

            for position in account_data['positions']:
                if position['unrealizedProfit'] != '0.00000000':
                    self.close_trade(position['symbol'], position['positionAmt'])

    def run_before(self):
        account_data = self.get_account_data()
        if not account_data['canTrade']:
            raise AccountCanNotTrade
