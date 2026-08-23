#!/usr/bin/env python3
"""
PDF Magic App — умный лаунчер.
Проверяет и устанавливает всё необходимое на чистой машине,
затем запускает сервер.

Требуется только Python 3.10+ и uv.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
REQUIREMENTS = PROJECT_DIR / "requirements.txt"

BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  [{GREEN}OK{RESET}] {msg}")


def warn(msg: str) -> None:
    print(f"  [{YELLOW}!!{RESET}] {msg}")


def fail(msg: str) -> None:
    print(f"  [{RED}XX{RESET}] {msg}")


def step(msg: str) -> None:
    print(f"\n{CYAN}[{msg}]{RESET}")


def find_cmd(name: str) -> str | None:
    """Find an executable on PATH (Windows-aware)."""
    return shutil.which(name) or shutil.which(f"{name}.cmd") or shutil.which(f"{name}.exe")


# ─── 1. uv ──────────────────────────────────────────────────────────

def check_uv() -> bool:
    """Ensure uv is installed."""
    step("1/3  Проверка uv")
    if find_cmd("uv"):
        ver = subprocess.run(["uv", "--version"], capture_output=True, text=True, errors="replace").stdout.strip()
        ok(f"uv найден: {ver}")
        return True
    fail("uv не найден! Установите uv:")
    print(f"       {BOLD}winget install astral-sh.uv{RESET}")
    print(f"       или: https://docs.astral.sh/uv/getting-started/installation/")
    return False


# ─── 2. Python deps ────────────────────────────────────────────────

def install_python_deps() -> bool:
    """Install project Python dependencies via uv (idempotent)."""
    step("2/3  Python-зависимости")
    if not REQUIREMENTS.exists():
        warn("requirements.txt не найден — пропускаем")
        return True

    result = subprocess.run(
        ["uv", "pip", "install", "-r", str(REQUIREMENTS), "--python", sys.executable],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        ok("Зависимости установлены")
        return True
    fail(f"Ошибка установки Python-зависимостей: {result.stderr[-300:]}")
    return False


# ─── 3. Java check (optional, for converter) ──────────────────────

def check_java() -> None:
    """Check Java for ODL converter (non-blocking). Auto-detect common locations."""
    step("3/3  Проверка Java")
    java = find_cmd("java")

    # Auto-detect Java if not on PATH
    if not java:
        candidates = [
            Path("C:/Program Files/Eclipse Adoptium"),
            Path("C:/Program Files/Java"),
            Path("C:/Program Files (x86)/Java"),
            Path("C:/Program Files/Microsoft"),
            Path.home() / ".sdkman/candidates/java",
        ]
        for base in candidates:
            if base.exists():
                for d in sorted(base.iterdir(), reverse=True):
                    j = d / "bin" / "java.exe"
                    if j.exists():
                        java = str(j)
                        break
            if java:
                break

    if java:
        try:
            ver = subprocess.run(
                [java, "-version"],
                capture_output=True, text=True,
                stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
            ).stdout or ""
            ver_line = [l for l in ver.splitlines() if "version" in l.lower()]
            ok(f"Java найдена: {ver_line[0][:60] if ver_line else 'OK'}")
            # Add to PATH for this session so ODL can find it
            java_bin = str(Path(java).parent)
            if java_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = java_bin + os.pathsep + os.environ.get("PATH", "")
        except Exception:
            ok("Java найдена")
    else:
        warn("Java не найдена — Конвертер PDF не заработает")
        print("       Установите JDK 11+: https://adoptium.net")


# ─── Launch ────────────────────────────────────────────────────────

def launch() -> None:
    """Import and run app.main() directly — no subprocess needed."""
    print(f"\n{CYAN}{'=' * 60}{RESET}")
    print(f"  {BOLD}Запуск PDF Magic App{RESET}")
    print(f"  http://localhost:5000")
    print(f"{CYAN}{'=' * 60}{RESET}\n")

    # PATH changes made by check_java() are inherited — no subprocess barrier
    import app
    app.main()


# ─── Main ──────────────────────────────────────────────────────────

def main() -> None:
    print(f"{BOLD}{CYAN}PDF Magic App — Лаунчер{RESET}\n")

    if not check_uv():
        sys.exit(1)

    if not install_python_deps():
        sys.exit(1)

    check_java()

    launch()


if __name__ == "__main__":
    main()
