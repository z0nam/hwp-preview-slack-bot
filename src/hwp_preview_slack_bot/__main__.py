"""HWP preview bot for Slack.

Listens for `file_shared` events; if the shared file is .hwp/.hwpx, downloads it,
converts to PDF and DOCX via scripts/hwp2x.sh (LibreOffice + H2Orestart), and
re-uploads both files as a threaded reply in the same channel. Original HWP
stays attached.
"""

from __future__ import annotations

import logging
import os
import pathlib
import subprocess
import tempfile
import threading
import urllib.request
from typing import Any

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("hwp_preview_bot")

HWP_EXTS = {".hwp", ".hwpx"}
OUT_FORMATS = ("pdf", "docx")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONVERT_SH = REPO_ROOT / "scripts" / "hwp2x.sh"

# Two HWPs uploaded close together would otherwise race on LibreOffice's
# shared user profile — the second soffice attaches to the first as a client
# and one output silently fails to materialize (exit 0, no file written).
_convert_lock = threading.Lock()

def _download(url: str, dest: pathlib.Path, token: str) -> None:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp, dest.open("wb") as f:
        while chunk := resp.read(1024 * 64):
            f.write(chunk)


def _thread_ts_for_share(info: dict[str, Any], channel: str) -> str | None:
    shares = info.get("shares", {}) or {}
    for scope in ("public", "private"):
        bucket = shares.get(scope, {}) or {}
        entries = bucket.get(channel)
        if entries:
            ts = entries[0].get("ts")
            if ts:
                return ts
    return None


def build_app(bot_token: str) -> App:
    app = App(token=bot_token)

    @app.event("file_shared")
    def handle_file_shared(event: dict[str, Any], client, logger: logging.Logger) -> None:
        file_id = event.get("file_id")
        channel = event.get("channel_id")
        if not file_id or not channel:
            return

        info = client.files_info(file=file_id).get("file") or {}
        name = info.get("name") or ""
        ext = pathlib.Path(name).suffix.lower()
        if ext not in HWP_EXTS:
            log.debug("skip non-hwp file id=%s name=%s", file_id, name)
            return

        log.info("convert request file=%s channel=%s name=%s", file_id, channel, name)

        download_url = info.get("url_private_download") or info.get("url_private")
        if not download_url:
            log.warning("no download url for file %s", file_id)
            return

        thread_ts = _thread_ts_for_share(info, channel)

        with tempfile.TemporaryDirectory(prefix="hwp_bot_") as td:
            td_path = pathlib.Path(td)
            local_input = td_path / name
            try:
                _download(download_url, local_input, bot_token)
            except Exception as e:
                log.exception("download failed file=%s", file_id)
                client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f":warning: `{name}` 다운로드 실패: `{e}`",
                )
                return

            produced: list[pathlib.Path] = []
            failures: list[tuple[str, str]] = []
            with _convert_lock:
                for fmt in OUT_FORMATS:
                    result = subprocess.run(
                        [str(CONVERT_SH), fmt, str(local_input), str(td_path)],
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    out_path = local_input.with_suffix(f".{fmt}")
                    if result.returncode == 0 and out_path.exists():
                        produced.append(out_path)
                    else:
                        tail = (result.stderr or result.stdout or "").strip()[-500:]
                        log.warning(
                            "conversion failed file=%s fmt=%s rc=%s",
                            file_id, fmt, result.returncode,
                        )
                        failures.append((fmt, tail or "(no output)"))

            if not produced:
                detail = "\n".join(f"- {fmt}: {tail}" for fmt, tail in failures)
                client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f":warning: `{name}` 변환 실패\n```{detail}```",
                )
                return

            comment_parts = [
                ":page_facing_up: 자동 변환 미리보기 (원본 hwp는 위 첨부 그대로 사용)."
            ]
            if failures:
                missed = ", ".join(fmt.upper() for fmt, _ in failures)
                comment_parts.append(f":warning: {missed} 변환은 실패.")

            try:
                client.files_upload_v2(
                    channel=channel,
                    thread_ts=thread_ts,
                    file_uploads=[
                        {
                            "file": str(p),
                            "filename": p.name,
                            "title": f"{name} — {p.suffix.lstrip('.').upper()} 변환본",
                        }
                        for p in produced
                    ],
                    initial_comment="\n".join(comment_parts),
                )
                log.info(
                    "uploaded file=%s outputs=%s",
                    file_id, [p.name for p in produced],
                )
            except Exception:
                log.exception("upload failed file=%s", file_id)

    return app


def main() -> None:
    if not CONVERT_SH.exists():
        raise SystemExit(f"convert script not found: {CONVERT_SH}")
    bot_token = os.environ["SLACK_BOT_TOKEN"]
    app_token = os.environ["SLACK_APP_TOKEN"]
    app = build_app(bot_token)
    log.info("hwp-preview bot starting (socket mode)")
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
