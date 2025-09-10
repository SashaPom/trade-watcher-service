import traceback
from typing import Iterable

import tg_bot
from config import TELEGRAM_ADMIN_CHAT_ID
from watcher.exceptions import StopWatcher


def watcher_handle_exceptions(func):
    def wrapper(watcher, *args, **kwargs):
        try:
            return func(watcher, *args, **kwargs)
        except StopWatcher:
            pass
        # except (DuplicateWatcher, AccountCanNotTrade):
        #     pass
        except Exception:
            message = '\n'.join([
                f'{watcher.id} {watcher.name_}',
                traceback.format_exc(),
            ])
            tg_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, message)

        from watcher import Manager

        Manager.remove_watcher(watcher.id)

    return wrapper


def repeat_if_raised_exception(*exceptions: Iterable[Exception], tries_count: int = 3):
    def wrapper(func):
        def wrapper_(watcher, *args, **kwargs):
            for _ in range(tries_count):
                try:
                    return func(watcher, *args, **kwargs)
                except exceptions as e:
                    raised_exception = e

                    message = f'({getattr(watcher, "exchange_name", None)}, {watcher.id}, {watcher.name_})\n' \
                              f'[{e.__class__.__name__}] {e}'
                    tg_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, message)

            raise raised_exception

        return wrapper_

    return wrapper


def profile_to_kwargs_for_watcher(profile: dict) -> dict:
    return {
        "id_": int(profile["id"]),
        "name_": profile["name"],
        "clear_checking_time_str": profile.get("refresh_time"),
        "lose_percent_limit": profile.get("lose_percent_limit"),
        "lose_amount_limit": profile.get("lose_amount_limit"),
        "lose_streak_limit": profile.get("lose_streak_limit"),
        "telegram_chat_id": profile.get("telegram_chat_id"),
    }

