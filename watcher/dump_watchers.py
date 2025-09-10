from datetime import datetime
from decimal import Decimal

from config import URL_PROFILES, DATETIME_FORMAT
from dump import dump_watcher_profiles, load_watcher_profiles
from utils import request_to_main, get_now
from watcher import Manager


def dump_watchers():
    dump_watcher_profiles(Manager.get_all_watchers())
    print('DUMP WAS CREATED!')


def load_watchers():
    dump = load_watcher_profiles()
    profiles = request_to_main(URL_PROFILES) or []

    for profile in profiles:
        dump_ = dump.get(str(profile['id']))

        watcher = Manager.create_watcher(profile)

        if dump_:
            try:
                next_clear_checking_datetime = datetime.strptime(
                    dump_['next_clear_checking_datetime'],
                    DATETIME_FORMAT
                )
            except:
                next_clear_checking_datetime = None

            if next_clear_checking_datetime is None \
                    or next_clear_checking_datetime \
                    and next_clear_checking_datetime > get_now():
                watcher.max_balance = Decimal(dump_['max_balance'])
                watcher.lose_streak = dump_['lose_streak']
                watcher.is_blocked = dump_['is_blocked']

            watcher.start()
