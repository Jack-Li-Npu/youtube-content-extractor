import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import main
from app.douyin_service import (
    DouyinManager,
    Job,
    caption_records,
    find_video,
    inspect_video,
    normalize_url,
    safe_media_url,
)
from app.transcript_service import ExtractionError

VIDEO = "7685972770793999667"
URL = f"https://www.douyin.com/video/{VIDEO}"


@pytest.mark.parametrize(
    "value", [URL, f"https://www.douyin.com/jingxuan?modal_id={VIDEO}", f"https://douyin.com/video/{VIDEO}/"]
)
def test_douyin_url_identity(value):
    assert normalize_url(value) == (URL, VIDEO)


def test_short_url_requires_normal_browser_resolution():
    assert normalize_url("https://v.douyin.com/abc123/") == ("https://v.douyin.com/abc123/", "")


@pytest.mark.parametrize(
    "value",
    [
        "http://www.douyin.com/video/" + VIDEO,
        "https://douyin.com.evil.test/video/" + VIDEO,
        "https://user:secret@douyin.com/video/" + VIDEO,
        "https://douyin.com:bad/video/" + VIDEO,
        "https://douyin.com/user/someone",
        "file:///etc/passwd",
        "https://[broken",
        "https://127.0.0.1/video/" + VIDEO,
    ],
)
def test_rejects_invalid_and_non_video_urls(value):
    with pytest.raises(ExtractionError) as error:
        normalize_url(value)
    assert error.value.code == "invalid_url"


def fixture_video():
    return {
        "aweme_id": VIDEO,
        "desc": "Public title <script>",
        "author": {"nickname": "Creator"},
        "video": {
            "duration": 1891861,
            "bit_rate": [
                {
                    "bit_rate": 10000,
                    "play_addr": {"width": 3840, "height": 2160, "url_list": ["https://v.douyinvod.com/4k"]},
                },
                {
                    "bit_rate": 1000,
                    "play_addr": {
                        "width": 1280,
                        "height": 720,
                        "url_list": ["https://v.douyinvod.com/720", "http://127.0.0.1/private"],
                    },
                },
            ],
            "subtitleInfos": [{"LanguageCodeName": "en", "Url": "https://video.snssdk.com/captions"}],
        },
    }


def test_matches_only_requested_video_and_prefers_moderate_media():
    target = fixture_video()
    other = {**target, "aweme_id": "7685972770793999668"}
    data = {"aweme_list": [other, target], "account": {"private": "not retained"}}
    assert find_video(data, VIDEO) is target
    assert find_video(data, "missing") is None
    inspected = inspect_video(target)
    assert inspected["duration"] == 1891.861
    assert inspected["_media_urls"] == ["https://v.douyinvod.com/720", "https://v.douyinvod.com/4k"]
    assert inspected["tracks"][0]["language"] == "en"
    job = Job("random", URL, VIDEO, True, Path("/unused"), video=inspected)
    public = json.dumps(job.public())
    assert "_media_urls" not in public and "_url" not in public
    assert "video.snssdk.com" not in public and "account" not in public


@pytest.mark.parametrize(
    "value",
    [
        "https://douyinvod.com.evil.test/a",
        "http://v.douyinvod.com/a",
        "https://127.0.0.1/a",
        "https://user:secret@v.douyinvod.com/a",
        "https://v.douyinvod.com:bad/a",
    ],
)
def test_media_url_guard(value):
    assert not safe_media_url(value)


def test_caption_json_and_vtt_preserve_fractional_actual_durations():
    expected = [{"start": 3601.125, "duration": 4.375, "text": "Hello 世界"}]
    assert (
        caption_records(
            json.dumps({"utterances": [{"start_time": 3601125, "end_time": 3605500, "text": "Hello 世界"}]})
        )
        == expected
    )
    assert caption_records("WEBVTT\n\n00:01:01.125 --> 00:01:05.500\nHello 世界")[0]["duration"] == 4.375
    assert caption_records("1\n01:00:01,125 --> 01:00:05,500\nHello 世界") == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "<html>Verification</html>",
        '{"utterances":[]}',
        '{"utterances":[{"start_time":0,"end_time":0,"text":"Hi"}]}',
        '{"utterances":[{"start_time":0,"end_time":NaN,"text":"Hi"}]}',
    ],
)
def test_empty_and_invalid_captions_fail_explicitly(text):
    with pytest.raises(ExtractionError) as error:
        caption_records(text)
    assert error.value.code == "captions_invalid"


def test_rejects_unsafe_redirect_before_following_it(tmp_path, monkeypatch):
    response = MagicMock()
    response.__enter__.return_value = response
    response.is_redirect = True
    response.headers = {"Location": "http://127.0.0.1/private"}
    session = MagicMock()
    session.get.return_value = response
    monkeypatch.setattr("app.douyin_service.requests.Session", lambda: session)
    context = MagicMock()
    context.cookies.return_value = []
    with pytest.raises(ExtractionError) as error:
        DouyinManager()._download(
            Job("job", URL, VIDEO, True, tmp_path), context, "https://v.douyinvod.com/video", tmp_path / "video", 100
        )
    assert error.value.code == "media_address_rejected"
    assert session.get.call_count == 1
    session.close.assert_called_once()


def test_manual_confirmation_required_and_single_job_isolated(tmp_path, monkeypatch):
    manager = DouyinManager()
    manager.job = Job("unguessable", URL, VIDEO, True, tmp_path, state="opening_browser")
    with pytest.raises(ExtractionError) as error:
        manager.confirm("unguessable")
    assert error.value.code == "job_not_waiting"
    assert not manager.job.action.is_set()
    manager.job.state = "waiting_verification"
    with pytest.raises(ExtractionError):
        manager.get("different")
    with pytest.raises(ExtractionError) as error:
        manager.start(URL)
    assert error.value.code == "douyin_busy"
    manager.confirm("unguessable")
    assert manager.job.action.is_set()
    manager.cancel("unguessable")
    assert manager.job.cancelled.is_set()
    manager.shutdown()
    assert not tmp_path.exists()


def test_api_protects_origin_and_viewer_escapes_source_title(tmp_path, monkeypatch):
    manager = DouyinManager()
    media = tmp_path / "source.mp4"
    media.write_bytes(b"synthetic-video")
    manager.job = Job(
        "unguessable",
        URL,
        VIDEO,
        True,
        tmp_path,
        state="completed",
        media=media,
        video={"title": "</title><script>bad()</script>", "tracks": []},
        result={"platform": "douyin"},
    )
    monkeypatch.setattr(main, "manager", manager)
    client = TestClient(main.app, base_url="http://127.0.0.1:8003")
    response = client.post("/api/douyin/jobs", json={"url": URL}, headers={"Origin": "https://evil.test"})
    assert response.status_code == 403
    status = client.get("/api/douyin/jobs/unguessable").json()
    assert client.get("/api/douyin/current-job").json()["job"] == status
    assert status["result"]["local_viewer_url"] == "http://127.0.0.1:8003/api/douyin/jobs/unguessable/viewer"
    viewer = client.get("/api/douyin/jobs/unguessable/viewer")
    assert "<script>bad()</script>" not in viewer.text
    assert "&lt;script&gt;" in viewer.text
    assert "frame-ancestors 'none'" in viewer.headers["Content-Security-Policy"]
    assert client.get("/api/douyin/jobs/different/video").status_code == 404
    response = client.get("/api/douyin/jobs/unguessable/video", headers={"Range": "bytes=0-8"})
    assert response.status_code == 206 and response.content == b"synthetic"


@pytest.mark.parametrize("needs_verification", [False, True])
def test_normal_playback_one_confirmation_runs_through_caption_export(tmp_path, monkeypatch, needs_verification):
    import playwright.sync_api

    manager = DouyinManager()
    job = Job("id", URL, VIDEO, False, tmp_path)
    manager.job = job
    context, page, response = MagicMock(), MagicMock(), MagicMock()
    context.pages = [page]
    response.url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
    response.headers = {"content-type": "application/json"}
    response.body.return_value = json.dumps({"aweme_detail": fixture_video()}).encode()
    page.locator.return_value.all_text_contents.return_value = []
    navigations = []

    def navigate(*args, **kwargs):
        navigations.append(args[0])
        if not needs_verification or len(navigations) > 1:
            context.on.call_args[0][1](response)

    page.goto.side_effect = navigate
    browser = MagicMock()
    browser.__enter__.return_value.chromium.launch_persistent_context.return_value = context
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", lambda: browser)
    monkeypatch.setenv("DOUYIN_BROWSER_PROFILE", str(tmp_path / "profile"))

    def wait(current, _page):
        assert needs_verification and current.state == "waiting_verification"
        manager.confirm(current.id)

    monkeypatch.setattr(manager, "_wait", wait)
    monkeypatch.setattr(manager, "_speech", lambda _: pytest.fail("captions should skip speech"))
    monkeypatch.setattr(
        manager,
        "_download",
        lambda _job, _context, _url, path, _limit: path.write_text(
            "1\n00:00:01,125 --> 00:00:05,500\nComplete caption text"
        ),
    )
    manager._run(job)
    assert job.state == "completed"
    assert job.result["source"] == "platform"
    assert job.result["plain_text"] == "Complete caption text"
    assert job.result["manual_verification_confirmed"] is needs_verification
    assert len(navigations) == (2 if needs_verification else 1)
    context.close.assert_called()


@pytest.mark.parametrize("allow_asr", [True, False])
def test_speech_flow_respects_opt_out_and_retries_audio_variant(tmp_path, monkeypatch, allow_asr):
    import playwright.sync_api

    manager = DouyinManager()
    job = Job("id", URL, VIDEO, allow_asr, tmp_path)
    manager.job = job
    data = fixture_video()
    data["video"]["subtitleInfos"] = []
    context, page, response = MagicMock(), MagicMock(), MagicMock()
    context.pages = [page]
    response.url = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
    response.headers = {"content-type": "application/json"}
    response.body.return_value = json.dumps(data).encode()
    page.goto.side_effect = lambda *args, **kwargs: context.on.call_args[0][1](response)
    browser = MagicMock()
    browser.__enter__.return_value.chromium.launch_persistent_context.return_value = context
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", lambda: browser)
    monkeypatch.setenv("DOUYIN_BROWSER_PROFILE", str(tmp_path / "profile"))
    setup = MagicMock()
    monkeypatch.setattr("app.douyin_service.check_setup", setup)
    probe = MagicMock(side_effect=[ExtractionError("no_audio", "no audio", 422), 10.125])
    monkeypatch.setattr("app.douyin_service.probe_video", probe)
    downloads = []

    def download(_job, _context, url, path, _limit):
        downloads.append(url)
        path.write_bytes(b"video")

    monkeypatch.setattr(manager, "_download", download)
    monkeypatch.setattr(manager, "_wait", lambda *_: pytest.fail("no manual step required for normal playback"))
    monkeypatch.setattr(
        "app.douyin_service.transcribe_job",
        lambda current: (
            {
                "segments": [{"start": 0.125, "duration": 9, "text": "Full speech", "quality_flags": []}],
                "metadata": {"language": "en"},
            }
            if current.audio_validated
            else pytest.fail("must check audio")
        ),
    )
    manager._run(job)
    if not allow_asr:
        assert job.state == "failed" and job.code == "captions_not_found"
        assert job.result is None and job.media is None and downloads == []
        setup.assert_not_called()
        probe.assert_not_called()
        return
    assert job.state == "completed" and job.result["source"] == "asr"
    assert downloads == ["https://v.douyinvod.com/720", "https://v.douyinvod.com/4k"]
    assert job.result["duration"] == 10.125
