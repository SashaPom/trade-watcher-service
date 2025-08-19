import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DUMP_WATCHER_PROFILES = os.path.join(BASE_DIR, 'dumps', 'dump_watcher_profiles.json')
