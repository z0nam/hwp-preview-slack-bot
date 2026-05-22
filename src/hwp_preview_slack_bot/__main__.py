"""HWP preview bot for Slack.

Listens for `file_shared` events; if the shared file is .hwp/.hwpx, downloads it,
converts to PDF and DOCX via scripts/hwp2x.sh (LibreOffice + H2Orestart), and
re-uploads both files as a threaded reply in the same channel. Original HWP
stays attached.

Also listens for `message_deleted` events: when the original upload is deleted,
the bot deletes its own preview reply too, so non-admin uploaders aren't left
with an orphaned preview they can't remove. Deleting a message that still has
thread replies leaves a tombstone, so the thread (and our reply) remains
readable — we just scan it and remove our own messages. No state to persist.
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


def _had_hwp_attachment(message: dict[str, Any]) -> bool:
    for f in message.get("files", []) or []:
        if pathlib.Path(f.get("name") or "").suffix.lower() in HWP_EXTS:
            return True
    return False


# Errors that simply mean "the thread/message is already gone" — expected when
# we delete the last reply and Slack then drops the tombstoned parent.
_GONE_ERRORS = {"thread_not_found", "message_not_found", "channel_not_found"}


def _bot_reply_tss(client, channel: str, thread_ts: str, bot_user_id: str) -> list[str]:
    """All message ts in ``thread_ts`` authored by the bot (excludes parent)."""
    try:
        resp = client.conversations_replies(channel=channel, ts=thread_ts, limit=100)
    except Exception as e:
        if getattr(e, "response", {}).get("error") in _GONE_ERRORS:
            return []
        log.exception("conversations_replies failed channel=%s ts=%s", channel, thread_ts)
        return []
    return [
        m.get("ts")
        for m in (resp.get("messages") or [])
        if m.get("ts") != thread_ts and m.get("user") == bot_user_id and m.get("ts")
    ]


def _parent_deleted(client, channel: str, thread_ts: str) -> bool:
    try:
        resp = client.conversations_replies(channel=channel, ts=thread_ts, limit=1)
    except Exception:
        return False
    msgs = resp.get("messages") or []
    return not msgs or msgs[0].get("subtype") == "tombstone"


def _delete_replies(client, channel: str, reply_tss: list[str], reason: str) -> None:
    for ts in reply_tss:
        try:
            client.chat_delete(channel=channel, ts=ts)
            log.info("deleted preview reply channel=%s reply=%s (%s)", channel, ts, reason)
        except Exception as e:
            if getattr(e, "response", {}).get("error") != "message_not_found":
                log.exception("failed to delete reply channel=%s reply=%s", channel, ts)


def build_app(bot_token: str) -> App:
    app = App(token=bot_token)
    bot_user_id = app.client.auth_test().get("user_id")

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
                return

            # Race guard: if the uploader deleted the original while we were
            # converting (~10s), the message_deleted event already fired before
            # this reply existed. Our reply is now orphaned under a tombstone —
            # detect that and clean it up right away.
            if thread_ts and _parent_deleted(client, channel, thread_ts):
                _delete_replies(
                    client, channel,
                    _bot_reply_tss(client, channel, thread_ts, bot_user_id),
                    reason="original deleted during conversion",
                )

    @app.event("message")
    def handle_message(event: dict[str, Any], client, logger: logging.Logger) -> None:
        # Deleting a message arrives as one of two events:
        #   - message_deleted: the message had NO thread replies (fully removed).
        #   - message_changed whose new message is a "tombstone": it HAD replies,
        #     so Slack keeps the thread and just blanks the parent. Our preview
        #     is a reply, so an original we care about almost always takes this
        #     second path — handling only message_deleted misses every real case.
        subtype = event.get("subtype")
        channel = event.get("channel")
        if subtype == "message_deleted":
            deleted_ts = event.get("deleted_ts")
            prev = event.get("previous_message") or {}
        elif subtype == "message_changed" and (event.get("message") or {}).get("subtype") == "tombstone":
            deleted_ts = (event.get("message") or {}).get("ts")
            prev = event.get("previous_message") or {}
        else:
            return
        if not channel or not deleted_ts:
            return

        # Loop guard: never react to deletion of our own messages.
        if prev.get("user") == bot_user_id:
            return
        # When we delete the last reply, Slack drops the tombstoned parent and
        # sends a follow-up message_deleted whose prior message is that
        # tombstone — nothing left to do, and its thread is already gone.
        if prev.get("subtype") == "tombstone":
            return
        # If the deleted message had attachments and none were HWP, it isn't an
        # original we previewed. (No file info → fall through and scan to be safe.)
        files = prev.get("files")
        if files is not None and not _had_hwp_attachment(prev):
            return

        reply_tss = _bot_reply_tss(client, channel, deleted_ts, bot_user_id)
        if not reply_tss:
            return
        log.info(
            "original deleted channel=%s ts=%s; removing %d preview reply(ies)",
            channel, deleted_ts, len(reply_tss),
        )
        _delete_replies(client, channel, reply_tss, reason="original deleted")

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
