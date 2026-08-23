#!/usr/bin/env python3
"""
PDF Magic App — исполнительная документация в строительстве.
.env → logging → CORS → SPA → blueprints → Waitress.
"""

import logging
import os
import sys
import threading
import webbrowser

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from routes import register_blueprints
from routes.core import (
    APP_DIR,
    MATERIALS_DIR,
    REACT_DIST,
    ensure_app_dirs,
    logger,
)
from utils.database import init_converter_db, init_db, init_requisites_db

logger.info("=" * 60)
logger.info("Запуск PDF Magic App")
logger.info("=" * 60)

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=100 * 1024 * 1024,
    SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32).hex()),
)
CORS(
    app,
    origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)

logging.getLogger("werkzeug").setLevel(logging.WARNING)


# Request logging
@app.before_request
def log_request_start():
    if request.path.startswith("/api/"):
        logger.info(f">>> {request.method} {request.path}")


@app.after_request
def log_request_end(response):
    if request.path.startswith("/api/"):
        logger.info(f"<<< {request.method} {request.path} -> {response.status_code}")
    return response


# ── HTML page routes (Jinja2 templates) ──
@app.route("/")
def index():
    return render_template("dashboard.html", page="dashboard")

@app.route("/directories/create")
def directories_page():
    return render_template("directories.html", page="directories")

@app.route("/converter")
def converter_page():
    return render_template("converter.html", page="converter")

@app.route("/aocr")
def aocr_page():
    return render_template("aocr.html", page="aocr")

@app.route("/requisites")
def requisites_page():
    return render_template("requisites.html", page="requisites")

@app.route("/rules")
def rules_page():
    return render_template("rules.html", page="rules")

@app.route("/materials")
def materials_page():
    return render_template("materials.html", page="materials")


# ── Health check ──
@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok"})


# ── Static files (vendored JS) ──
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# Register all blueprint routes
register_blueprints(app)


def _kill_port_5000():
    """Убивает зомби-процессы на порту 5000 (Windows)."""
    import subprocess

    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5, errors="replace")
        for line in result.stdout.splitlines():
            if ":5000" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                # Validate PID is numeric only
                if not pid.isdigit():
                    continue
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)
                logger.info(f"Зомби-процесс убит: PID {pid}")
    except Exception:
        pass


def open_browser():
    try:
        webbrowser.open("http://localhost:5000")
    except Exception as e:
        logger.error(f"Не удалось открыть браузер: {e}")


def main() -> None:
    """Launch the app. Starts Flask+Waitress directly (not as subprocess)."""
    import time

    _kill_port_5000()
    time.sleep(0.5)

    ensure_app_dirs()
    if not MATERIALS_DIR.exists():
        MATERIALS_DIR.mkdir(parents=True)
    init_db()
    init_converter_db()
    init_requisites_db()

    logger.info(f"Целевая папка: {APP_DIR}")
    logger.info("Веб-интерфейс: http://localhost:5000")
    logger.info("=" * 60)

    threading.Timer(1.5, open_browser).start()

    try:
        import signal

        from waitress import create_server

        logger.info("Production сервер: waitress")
        _server = create_server(app, host="127.0.0.1", port=5000)

        def _shutdown_handler(signum=None, frame=None):
            logger.info("Graceful shutdown...")
            try:
                _server.close()
            except Exception:
                pass
            logger.info("Сервер остановлен.")
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown_handler)

        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32

            @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
            def _console_handler(ctrl_type):
                if ctrl_type in (0, 2, 5, 6):
                    threading.Thread(target=_shutdown_handler, daemon=True).start()
                    return 1
                return 0

            kernel32.SetConsoleCtrlHandler(_console_handler, 1)

        _server.run()
    except ImportError:
        logger.info("Waitress не найден, запуск dev-сервера Flask")
        app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
