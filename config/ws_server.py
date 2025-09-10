import os

WS_ADDRESS = (os.getenv('WS_ADDRESS') or '').strip()
WS_PORT    = int(os.getenv("WS_PORT", "0"))

URL_PROFILES = os.getenv(
    "URL_PROFILES",
    "http://gateway:8080/api/py/dj/tw/api/watcher/profiles/"
)
URL_UPDATE_PROFILE = os.getenv(
    "URL_UPDATE_PROFILE",
    "http://gateway:8080/api/py/dj/tw/api/profile/update/"
)