import os
import ssl
import sys
import pathlib
import threading
import http.server
import socketserver

import ws
from config import WS_ADDRESS, WS_PORT, SSL_CERTFILE, SSL_KEYFILE, EXCHANGE_NAME
from handler import handler_watcher, update_profiles
from watcher.dump_watchers import load_watchers, dump_watchers
import tg_bot

def _start_health_server():
    class _H(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(404)
                self.end_headers()

    port = int(os.getenv("HEALTH_PORT", "9002"))
    with socketserver.TCPServer(("0.0.0.0", port), _H) as httpd:
        httpd.serve_forever()


if os.getenv("HEALTH_ENABLED", "false").lower() == "true":
    threading.Thread(target=_start_health_server, daemon=True).start()


def get_ssl_context():
    """
    Пытаемся поднять TLS только если оба пути указывают на РЕАЛЬНЫЕ ФАЙЛЫ.
    Приоритет: переменные окружения, затем значения из config.
    Если что-то не так — возвращаем None и работаем по ws:// (без TLS).
    """
    cert = (os.getenv("SSL_CERTFILE") or SSL_CERTFILE or "").strip()
    key = (os.getenv("SSL_KEYFILE") or SSL_KEYFILE or "").strip()

    cert_p = pathlib.Path(cert)
    key_p = pathlib.Path(key)

    if cert_p.is_file() and key_p.is_file():
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(cert, key)
            print(f"[SSL] Using cert={cert} key={key}")
            return ctx
        except Exception as e:
            print(f"[SSL] Failed to load certs ({cert}, {key}): {e}", file=sys.stderr)
            return None
    else:
        # Диагностика, почему TLS не включён
        if cert and not cert_p.is_file():
            print(f"[SSL] SSL_CERTFILE is not a file or missing: {cert}", file=sys.stderr)
        if key and not key_p.is_file():
            print(f"[SSL] SSL_KEYFILE is not a file or missing: {key}", file=sys.stderr)
        return None


def main_():
    print(sys.argv)
    print(EXCHANGE_NAME)

    ssl_ctx = get_ssl_context()

    # Важно: ws.Server должен уметь принимать ssl=None (обычный ws://).
    # Если ssl_ctx не None, будет wss://
    server = ws.Server(
        handler_watcher,
        WS_ADDRESS,
        WS_PORT,
        ssl_ctx,
    )

    if '--load' in sys.argv:
        load_watchers()
    elif '--update' in sys.argv:
        update_profiles()

    try:
        update_profiles()
        server.run()
    except KeyboardInterrupt:
        dump_watchers()


if __name__ == '__main__':
    main_()
