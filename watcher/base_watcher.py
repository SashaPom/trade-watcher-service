import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, time as time_, timedelta
from decimal import Decimal
from itertools import repeat
from typing import Optional, Union, Iterable, Generator

import telegram
from utils import do_nothing, get_now
from watcher.exceptions import AccountCanNotTrade, StopWatcher
from watcher.utils import watcher_handle_exceptions


class BaseWatcher(ABC, threading.Thread):
    exchange_name: str

    id: int
    name_: str

    available_balance: Decimal() = Decimal()
    previous_balance: Decimal() = Decimal()
    balance: Decimal() = Decimal()
    un_pnl: Decimal() = Decimal()

    max_balance: Decimal() = Decimal()
    lose_streak: int = 0

    is_blocked: bool = False
    is_trade_before: bool = False
    is_trade_now: bool = False
    lose_amount_limit: Decimal() = None  # for max_balance
    lose_percent_limit: Decimal()  # for max_balance
    lose_streak_limit: int

    clear_checking_time_str = None
    lose_percent_limit_ = None
    lose_amount_limit_ = None
    lose_streak_limit_ = None

    next_clear_checking_datetime: Optional[datetime] = None

    telegram_chat_id: Union[int, str]

    checks: list
    sleep_time: int = 1
    min_loop_count: int = 60

    def __init__(self, *args, id_, name_, clear_checking_time_str: str = None,
                 lose_percent_limit: float = None, lose_amount_limit: float = None, lose_streak_limit: int = None,
                 telegram_chat_id: Union[int, str] = None, **kwargs):
        self.target = self.run

        self.id = id_
        self.name_ = name_

        self.checks = []

        self.telegram_chat_id = telegram_chat_id
        self.set_clear_checking_time(clear_checking_time_str)
        self.set_lose_percent_limit(lose_percent_limit)
        self.set_lose_amount_limit(lose_amount_limit)
        self.set_lose_streak_limit(lose_streak_limit)

        super().__init__(*args, name=id_, **kwargs)

    def set_clear_checking_time(self, clear_checking_time_str: Optional[str] = None):
        self.clear_checking_time_str = clear_checking_time_str

        if isinstance(clear_checking_time_str, str):
            try:
                clear_checking_time = time_(*[int(v) for v in clear_checking_time_str.split(':')])
            except (TypeError, ValueError):
                self.run_clear_checking_values = do_nothing
                return

            now = get_now()
            self.next_clear_checking_datetime = now.replace(
                hour=clear_checking_time.hour,
                minute=clear_checking_time.minute,
                second=clear_checking_time.second
            )
            if self.next_clear_checking_datetime < now:
                self.next_clear_checking_datetime += timedelta(days=1)

            self.run_clear_checking_values = self.run_clear_checking_values_

        else:
            self.next_clear_checking_datetime = None
            self.run_clear_checking_values = do_nothing

    def set_lose_amount_limit(self, lose_amount_limit: Optional[float] = None):
        self.lose_amount_limit_ = lose_amount_limit
        if isinstance(lose_amount_limit, (float, int)) and lose_amount_limit > 0:
            self.lose_amount_limit = Decimal(lose_amount_limit)
            if self.check_amount_limit not in self.checks:
                self.checks.append(self.check_amount_limit)
        elif self.check_amount_limit in self.checks:
            self.checks.remove(self.check_amount_limit)

    def set_lose_percent_limit(self, lose_percent_limit: Optional[float] = None):
        self.lose_percent_limit_ = lose_percent_limit
        if isinstance(lose_percent_limit, float) and 1 > lose_percent_limit > 0:
            self.lose_percent_limit = Decimal(lose_percent_limit)
            if self.check_percent_limit not in self.checks:
                self.checks.append(self.check_percent_limit)
        elif self.check_percent_limit in self.checks:
            self.checks.remove(self.check_percent_limit)

    def set_lose_streak_limit(self, lose_streak_limit: Optional[int] = None):
        self.lose_streak_limit_ = lose_streak_limit
        if isinstance(lose_streak_limit, int) and lose_streak_limit > 0:
            self.lose_streak_limit = lose_streak_limit
            if self.check_lose_streak not in self.checks:
                self.checks.append(self.check_lose_streak)
        elif self.check_lose_streak in self.checks:
            self.checks.remove(self.check_lose_streak)

    @abstractmethod
    def update_balance_(self):
        pass

    def update_balance(self):
        self.previous_balance = self.balance
        self.is_trade_before = self.is_trade_now

        self.update_balance_()

        self.is_trade_now = self.available_balance != self.balance
        self.max_balance = max(self.max_balance, self.balance)

        # print(self.available_balance, self.balance, self.un_pnl, self.is_trade_now, self.max_balance,
        #       self.lose_streak)

    @abstractmethod
    def close_trades(self):
        pass

    def clear_checking_values(self):
        print('clear_checking_values')
        self.lose_streak = 0
        self.max_balance = self.balance
        self.is_blocked = False

    def get_loop(self) -> Union[Iterable, Generator]:
        if self.next_clear_checking_datetime is None:
            return repeat(None)
        now = get_now()
        sleep = max((self.next_clear_checking_datetime - now).seconds // 2, self.min_loop_count)
        return range(sleep)

    # RUNNING

    def run_before(self):
        pass

    def run_clear_checking_values_(self):
        if get_now() > self.next_clear_checking_datetime:
            self.clear_checking_values()
            self.next_clear_checking_datetime += timedelta(days=1)

    def run_clear_checking_values(self):
        pass

    def run_not_blocked(self):
        print('run_not_blocked')
        for _ in self.get_loop():
            self.update_balance()
            if self.check():
                self.close_trades()
                self.is_blocked = True
                return
            time.sleep(self.sleep_time)

    def run_blocked(self):
        print('run_blocked')
        for _ in self.get_loop():
            self.update_balance()
            self.close_trades()
            time.sleep(self.sleep_time)

    @watcher_handle_exceptions
    def run(self):
        self.run_before()

        while True:

            self.run_clear_checking_values()

            if self.is_blocked:
                self.run_blocked()
            else:
                self.run_not_blocked()

    def __stop(self, *args, **kwargs):
        raise StopWatcher

    def stop(self):
        self.update_balance = self.__stop

    # CHECKING | True = closing trades

    def check(self) -> bool:
        for check_method in self.checks:
            if check_method():
                return True
        return False

    def check_percent_limit(self) -> bool:
        limit = self.max_balance * (1 - self.lose_percent_limit)
        balance = self.balance + self.un_pnl
        if balance <= limit:
            print('check_percent_limit')
            self.send_message(
                f'Blocked by Percent Limit. Balance: ~ {balance}'
            )
            return True
        return False

    def check_amount_limit(self) -> bool:
        limit = self.max_balance - self.lose_amount_limit
        balance = self.balance + self.un_pnl
        if balance <= limit:
            print('check_amount_limit')
            self.send_message(
                f'Blocked by Amount Limit. Balance: ~ {balance}'
            )
            return True
        return False

    def check_lose_streak(self) -> bool:
        if self.is_trade_before and not self.is_trade_now:
            if self.previous_balance > self.balance:
                self.lose_streak += 1
                if self.lose_streak >= self.lose_streak_limit:
                    print('check_lose_streak')
                    self.send_message(
                        f'Blocked by Lose Streak: {self.lose_streak}/{self.lose_streak_limit}'
                    )
                    return True
            else:
                self.lose_streak = 0
        return False

    def send_message(self, message: str):
        if self.telegram_chat_id:
            telegram.send_message(
                self.telegram_chat_id,
                f'({self.exchange_name}) [{self.name_}] {message}'
            )
