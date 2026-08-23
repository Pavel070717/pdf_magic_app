"""
Blueprint: /api/converter/* — PDF conversion via OpenDataLoader.
Real progress tracking through Java CLI stdout parsing + pypdf page count.
"""

import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from routes.core import APP_DIR, logger  # импорт APP_DIR перенесён сюда

converter_bp = Blueprint("converter", __name__)

CONVERTER_OUTPUT = APP_DIR / "Конвертор пдф"
CONVERTER_OUTPUT.mkdir(parents=True, exist_ok=True)

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
_last_progress_time: dict[str, float] = {}

ALLOWED_FORMATS = {"markdown", "json", "html", "text", "tagged-pdf"}


def _find_jar() -> Path:
    """Locate the bundled ODL JAR inside the installed package."""
    import importlib.resources as resources

    jar_ref = resources.files("opendataloader_pdf").joinpath(
        "jar", "opendataloader-pdf-cli.jar"
    )
    return Path(str(jar_ref))


@converter_bp.route("/api/converter/convert", methods=["POST"])
def convert_pdf():
    from utils.database import add_conversion

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename or not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Только PDF-файлы"}), 400

    output_format = request.form.get("format", "markdown")
    if output_format not in ALLOWED_FORMATS:
        return (
            jsonify(
                {"success": False, "error": f"Недопустимый формат: {output_format}"}
            ),
            400,
        )

    job_id = str(uuid.uuid4())[:8]
    safe_name = (
        "".join(c for c in Path(uploaded.filename).stem if c.isalnum() or c in "._- ()")
        or "doc"
    )
    dest = CONVERTER_OUTPUT / f"{safe_name}.pdf"
    counter = 1
    while dest.exists():
        dest = CONVERTER_OUTPUT / f"{safe_name}_{counter}.pdf"
        counter += 1

    uploaded.save(str(dest))
    logger.info(f"PDF сохранён для конвертации: {dest}")

    # Count pages upfront with pypdf for accurate progress tracking
    page_count = 0
    try:
        from pypdf import PdfReader

        page_count = len(PdfReader(str(dest)).pages)
    except Exception:
        pass

    job = {
        "id": job_id,
        "filename": uploaded.filename,
        "output_format": output_format,
        "status": "pending",
        "progress": 0,
        "stage": "Загрузка...",
        "page_count": page_count,
        "current_page": 0,
        "error": None,
        "result_path": None,
        "result_text": None,
        "result_size": 0,
    }

    with _jobs_lock:
        _jobs[job_id] = job

    conv_id = add_conversion(uploaded.filename, output_format, str(dest))
    job["db_id"] = conv_id

    thread = threading.Thread(
        target=_run_conversion, args=(job_id, dest, output_format)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "job_id": job_id})


def _update_job(job_id: str, **kwargs) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job:
            job.update(kwargs)


def _run_conversion(job_id: str, pdf_path: Path, fmt: str) -> None:
    """Run ODL Java CLI in streaming mode, parse stdout for real progress."""

    _update_job(job_id, status="running", progress=5, stage="Инициализация...")
    start_time = time.time()

    try:
        jar = _find_jar()

        # Map format to CLI flag
        fmt_flag = {"tagged-pdf": "tagged-pdf"}.get(fmt, fmt)

        cmd = [
            "java",
            "-Djava.awt.headless=true",
            "-jar",
            str(jar),
            str(pdf_path),
            "-o",
            str(CONVERTER_OUTPUT),
            "-f",
            fmt_flag,
        ]

        _update_job(job_id, progress=10, stage="Запуск обработчика...")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        total_pages = 0
        output_written = False

        for line in proc.stdout:
            line_s = line.rstrip()

            # Parse total pages: "INFO: Number of pages: 42"
            m = re.search(r"Number of pages:\s*(\d+)", line_s)
            if m:
                total_pages = int(m.group(1))
                _update_job(
                    job_id,
                    page_count=total_pages,
                    progress=15,
                    stage=f"Найдено страниц: {total_pages}",
                )
                continue

            # Parse processing start
            if "Processing" in line_s and "pages" in line_s:
                _update_job(
                    job_id, progress=25, stage=f"Обработка {total_pages} стр...."
                )
                continue

            # Detect output file creation → near done
            if "Created" in line_s or "MarkdownGenerator" in line_s:
                output_written = True
                _update_job(job_id, progress=92, stage="Формирование вывода...")
                continue

            # Progress via elapsed time (throttled — update at most 2×/sec)
            if total_pages > 0 and not output_written:
                now = time.time()
                last_pb = _last_progress_time.get(job_id, 0)
                if now - last_pb < 0.5:
                    continue
                _last_progress_time[job_id] = now
                elapsed = now - start_time
                # Fixed per-page estimate: 2 seconds. The previous formula
                # (elapsed / (elapsed / total_pages)) always gave total_pages,
                # making the progress bar jump instantly from 25 % to ~90 %.
                fake_processed = min(elapsed / 2.0, total_pages - 1)
                pct = int(25 + (fake_processed / total_pages) * 65)
                if pct < 25:
                    pct = 25
                if pct > 90:
                    pct = 90
                _update_job(
                    job_id,
                    progress=pct,
                    current_page=min(int(fake_processed) + 1, total_pages),
                    stage=f"Страница {min(int(fake_processed) + 1, total_pages)} из {total_pages}",
                )

        proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)

        _update_job(job_id, progress=95, stage="Проверка результата...")

        # Locate output file
        stem = pdf_path.stem
        ext_map = {
            "markdown": ".md",
            "json": ".json",
            "html": ".html",
            "text": ".txt",
            "tagged-pdf": "-tagged.pdf",
        }
        ext = ext_map.get(fmt, f".{fmt}")
        result_file = CONVERTER_OUTPUT / f"{stem}{ext}"

        if result_file.exists():
            result_size = result_file.stat().st_size
            result_text = None
            if fmt in ("markdown", "text", "json", "html"):
                try:
                    result_text = result_file.read_text(
                        encoding="utf-8", errors="replace"
                    )[:50000]
                except Exception:
                    pass
            _update_job(
                job_id,
                status="done",
                progress=100,
                stage="Готово",
                result_path=str(result_file),
                result_text=result_text,
                result_size=result_size,
            )
        else:
            # Try to find any output file
            candidates = list(CONVERTER_OUTPUT.glob(f"{stem}*"))
            found = [c for c in candidates if c != pdf_path]
            if found:
                rf = found[0]
                _update_job(
                    job_id,
                    status="done",
                    progress=100,
                    stage="Готово",
                    result_path=str(rf),
                    result_size=rf.stat().st_size,
                )
            else:
                _update_job(job_id, status="error", error="Файл результата не найден")

    except FileNotFoundError:
        _update_job(job_id, status="error", error="Java не найдена. Установите JDK 11+")

    except subprocess.CalledProcessError as e:
        logger.error(f"ODL exit code {e.returncode}")
        _update_job(
            job_id, status="error", error=f"Ошибка конвертации (код {e.returncode})"
        )

    except Exception as e:
        logger.exception(f"Ошибка конвертации {job_id}")
        _update_job(job_id, status="error", error=str(e)[:200])


@converter_bp.route("/api/converter/progress/<job_id>", methods=["GET"])
def get_progress(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    return jsonify({"success": True, "job": job})


@converter_bp.route("/api/converter/download/<job_id>", methods=["GET"])
def download_result(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job or not job.get("result_path"):
        return jsonify({"success": False, "error": "No result available"}), 404

    path = Path(job["result_path"])
    if not path.exists():
        return jsonify({"success": False, "error": "Result file not found"}), 404
    return send_file(str(path), as_attachment=True, download_name=path.name)


@converter_bp.route("/api/converter/history", methods=["GET"])
def get_history():
    from utils.database import get_conversions

    try:
        rows = get_conversions()
        return jsonify({"success": True, "history": rows})
    except Exception as e:
        logger.exception("Ошибка истории конвертаций")
        return jsonify({"success": False, "error": str(e)}), 500


@converter_bp.route("/api/converter/history/<int:conv_id>", methods=["DELETE"])
def delete_history_entry(conv_id: int):
    from utils.database import delete_conversion

    try:
        if delete_conversion(conv_id):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
