"""Guards the fix for pasted Google Drive links being treated as uploads.

A Drive/Dropbox link to an .hwpx fires ``file_shared`` with an hwp-suffixed
name but is not a Slack-hosted upload; converting it only yields a false
``변환 실패``. ``_is_external_file`` must flag those so the handler skips them,
while leaving genuine uploads alone.
"""

from hwp_preview_slack_bot.__main__ import _is_external_file


def test_real_upload_is_not_external():
    info = {"name": "report.hwpx", "mode": "hosted", "is_external": False}
    assert _is_external_file(info) is False


def test_gdrive_link_flagged_by_is_external():
    info = {"name": "report.hwpx", "is_external": True, "external_type": "gdrive"}
    assert _is_external_file(info) is True


def test_external_mode_flagged():
    info = {"name": "report.hwpx", "mode": "external"}
    assert _is_external_file(info) is True


def test_missing_fields_default_to_not_external():
    # A minimal payload with neither field present must not be skipped.
    assert _is_external_file({"name": "report.hwpx"}) is False
