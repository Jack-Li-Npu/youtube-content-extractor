"""Observe one Douyin video's normal browser playback after manual verification.

No signature generation, challenge solving, private desktop code, or cookie export.
The browser owns login. Only a matching video's metadata is retained by the job.
"""

import html
import json
import logging
import math
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import requests
from playwright.sync_api import Error as BrowserError

from .speech_service import check_setup, probe_video, transcribe_job
from .transcript_service import ExtractionError

ROOT = Path(__file__).resolve().parents[2]
LOG = logging.getLogger(__name__)
TERMINAL = {"completed", "failed", "cancelled"}
MEDIA_DOMAINS = (
    "douyinvod.com",
    "douyin.com",
    "snssdk.com",
    "toutiaovod.com",
    "bytecdn.cn",
    "bytecdn.com",
    "ibytedtos.com",
)


def normalize_url(value):
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except (AttributeError, TypeError, ValueError) as exc:
        raise ExtractionError("invalid_url", "Paste a valid Douyin video link.", 400) from exc
    if parsed.scheme != "https" or parsed.hostname not in {"douyin.com", "www.douyin.com", "v.douyin.com"}:
        raise ExtractionError("invalid_url", "Paste an HTTPS Douyin video or share link.", 400)
    if parsed.username or parsed.password or port not in (None, 443):
        raise ExtractionError("invalid_url", "This Douyin link has an invalid address.", 400)
    query = parse_qs(parsed.query)
    match = re.fullmatch(r"/video/(\d{16,22})/?", parsed.path)
    identity = match.group(1) if match else (query.get("modal_id") or [""])[0]
    if re.fullmatch(r"\d{16,22}", identity):
        return f"https://www.douyin.com/video/{identity}", identity
    if parsed.hostname == "v.douyin.com" and re.fullmatch(r"/[A-Za-z0-9_-]{3,80}/?", parsed.path):
        return f"https://v.douyin.com{parsed.path}", ""
    raise ExtractionError("invalid_url", "Use an individual Douyin video link, not a profile or collection.", 400)


def safe_media_url(value):
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
            and bool(parsed.hostname)
            and any(parsed.hostname == domain or parsed.hostname.endswith("." + domain) for domain in MEDIA_DOMAINS)
        )
    except (TypeError, ValueError):
        return False


def find_video(data, identity, depth=0):
    if depth > 16:
        return None
    if isinstance(data, dict):
        if str(data.get("aweme_id", "")) == identity and isinstance(data.get("video"), dict):
            return data
        values = data.values()
    elif isinstance(data, list):
        values = data
    else:
        return None
    for value in values:
        match = find_video(value, identity, depth + 1)
        if match:
            return match
    return None


def inspect_video(data):
    video = data["video"]
    candidates = []
    for entry in video.get("bit_rate") or []:
        address = entry.get("play_addr") or {}
        if address.get("url_list"):
            # Prefer a moderate resolution for speech extraction; retain the
            # returned URLs rather than constructing private playback endpoints.
            edge = min(address.get("width") or 9999, address.get("height") or 9999)
            candidates.append((abs(edge - 720), entry.get("bit_rate") or 0, address))
    addresses = [row[2] for row in sorted(candidates, key=lambda row: row[:2])]
    addresses += [video.get("play_addr_h264") or {}, video.get("play_addr") or {}]
    urls = list(
        dict.fromkeys(url for address in addresses for url in address.get("url_list", []) if safe_media_url(url))
    )
    tracks = []
    infos = (data.get("subtitle_infos") or []) + (video.get("subtitleInfos") or [])
    infos += (video.get("subtitle") or {}).get("subtitleInfos") or []
    infos += (video.get("cla_info") or {}).get("caption_infos") or []
    for sticker in data.get("interaction_stickers") or []:
        infos += (sticker.get("auto_video_caption_info") or {}).get("auto_captions") or []
    for info in infos:
        address = info.get("Url") or info.get("url")
        if isinstance(address, dict):
            address = next(iter(address.get("url_list") or []), "")
        if not safe_media_url(address):
            continue
        language = (
            info.get("LanguageCodeName")
            or info.get("languageCodeName")
            or info.get("lang")
            or info.get("language")
            or "und"
        )
        if any(track["_url"] == address for track in tracks):
            continue
        tracks.append(
            {
                "id": f"platform:{len(tracks)}",
                "language": str(language),
                "name": str(language),
                "source": "platform",
                "_url": address,
            }
        )
    duration = float(video.get("duration") or data.get("duration") or 0) / 1000
    return {
        "platform": "douyin",
        "video_id": str(data["aweme_id"]),
        "title": str(data.get("desc") or "Douyin video"),
        "channel": str((data.get("author") or {}).get("nickname") or ""),
        "duration": duration,
        "url": f"https://www.douyin.com/video/{data['aweme_id']}",
        "tracks": tracks,
        "_media_urls": urls,
    }


def caption_records(text):
    """Read timed JSON utterances or SRT/WebVTT without fabricating durations."""
    records = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("utterances"), list):
        for cue in data["utterances"]:
            records.append(
                {
                    "start": float(cue["start_time"]) / 1000,
                    "duration": (float(cue["end_time"]) - float(cue["start_time"])) / 1000,
                    "text": str(cue.get("text") or ""),
                }
            )
    else:

        def seconds(value):
            parts = value.replace(",", ".").split(":")
            return sum(float(part) * 60**index for index, part in enumerate(reversed(parts)))

        for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
            lines = block.strip().splitlines()
            for index, line in enumerate(lines):
                match = re.match(r"([\d:. ,]+?)\s*-->\s*([\d:.,]+)", line)
                if match:
                    start, end = map(seconds, match.groups())
                    wording = html.unescape(re.sub(r"<[^>]+>", "", "\n".join(lines[index + 1 :])))
                    records.append({"start": start, "duration": end - start, "text": wording})
                    break
    if not records or any(
        not cue["text"].strip()
        or not math.isfinite(cue["start"] + cue["duration"])
        or cue["start"] < 0
        or cue["duration"] <= 0
        for cue in records
    ):
        raise ExtractionError(
            "captions_invalid",
            "The returned caption track has no usable timed text. Choose another track or use speech recognition.",
            422,
        )
    return records


@dataclass
class Job:
    id: str
    url: str
    identity: str
    allow_asr: bool
    directory: Path
    state: str = "opening_browser"
    message: str = "Opening Douyin for manual verification…"
    video: dict | None = None
    result: dict | None = None
    media: Path | None = None
    code: str = ""
    choice: str = ""
    audio_validated: bool = False
    manual_confirmed: bool = False
    worker_exit_code: int | None = None
    action: threading.Event = field(default_factory=threading.Event)
    cancelled: threading.Event = field(default_factory=threading.Event)
    show_browser: threading.Event = field(default_factory=threading.Event)

    def public(self):
        video = (
            None if self.video is None else {key: value for key, value in self.video.items() if not key.startswith("_")}
        )
        if video:
            video["tracks"] = [
                {key: value for key, value in track.items() if not key.startswith("_")} for track in video["tracks"]
            ]
        return {
            "id": self.id,
            "url": self.url,
            "state": self.state,
            "message": self.message,
            "code": self.code,
            "video": video,
            "result": self.result if self.state == "completed" else None,
            "can_retry_speech": self.state == "failed"
            and self.audio_validated
            and bool(self.media and self.media.is_file()),
            "diagnostic": {"code": self.code, "worker_exit_code": self.worker_exit_code} if self.code else None,
        }


class DouyinManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.job = None
        self.worker = None

    def start(self, url, allow_asr=True):
        normalized, identity = normalize_url(url)
        with self.lock:
            if self.job and self.job.state not in TERMINAL:
                raise ExtractionError(
                    "douyin_busy", "A Douyin extraction is running. Complete or cancel it first.", 409
                )
            if self.job:
                shutil.rmtree(self.job.directory, ignore_errors=True)
            job = Job(
                secrets.token_urlsafe(24),
                normalized,
                identity,
                allow_asr,
                Path(tempfile.mkdtemp(prefix="transcript-douyin-")),
            )
            os.chmod(job.directory, 0o700)
            self.job = job
            self.worker = threading.Thread(target=self._run, args=(job,), daemon=True)
            self.worker.start()
            return job.public()

    def get(self, identity):
        if not self.job or identity != self.job.id:
            raise ExtractionError("job_missing", "This extraction has ended. Start a new one.", 404)
        return self.job

    def confirm(self, identity, track_id=""):
        job = self.get(identity)
        if job.state not in {"waiting_verification", "waiting_track"}:
            raise ExtractionError("job_not_waiting", "This extraction is not waiting for confirmation.", 409)
        job.choice = track_id
        if job.state == "waiting_verification":
            job.manual_confirmed = True
        job.state, job.message = "reading_video", "Verification complete. The remaining steps run automatically…"
        job.action.set()
        return job.public()

    def reveal_browser(self, identity):
        job = self.get(identity)
        if job.state != "waiting_verification":
            raise ExtractionError("job_not_waiting", "The verification window is not needed at this step.", 409)
        job.show_browser.set()
        return job.public()

    def retry_speech(self, identity):
        with self.lock:
            job = self.get(identity)
            if not job.public()["can_retry_speech"]:
                raise ExtractionError(
                    "retry_unavailable", "This job has no acquired audio to reuse. Retry extraction.", 409
                )
            if self.worker:
                self.worker.join(timeout=2)
            job.code, job.worker_exit_code = "", None
            job.cancelled.clear()
            job.state, job.message = "transcribing", "Retrying speech recognition on the acquired video…"
            self.worker = threading.Thread(target=self._retry_speech, args=(job,), daemon=True)
            self.worker.start()
            return job.public()

    def _retry_speech(self, job):
        try:
            self._speech(job)
        except ExtractionError as exc:
            self._fail(job, exc)
        except Exception as exc:  # noqa: BLE001 -- worker boundary, do not expose raw worker output
            LOG.warning("Speech retry failed (%s)", type(exc).__name__)
            self._fail(
                job,
                ExtractionError(
                    "speech_failed",
                    "Speech recognition failed. Retry speech recognition; the acquired video is kept.",
                    422,
                ),
            )

    def _complete(self, job, lines, source, provider, language, track_id):
        job.result = {
            **{key: value for key, value in job.video.items() if not key.startswith("_") and key != "tracks"},
            "success": True,
            "source": source,
            "provider": provider,
            "language": language,
            "track_id": track_id,
            "generated_at": time.time(),
            "transcript_lines": lines,
            "plain_text": "\n".join(cue["text"] for cue in lines),
            "acquisition_provider": "playwright-browser",
            "manual_verification_confirmed": job.manual_confirmed,
        }
        for cue in lines:
            total = int(cue["start"])
            cue["seconds"] = total
            cue["timestamp"] = (
                f"{total // 3600:02}:{total // 60 % 60:02}:{total % 60:02}"
                if total >= 3600
                else f"{total // 60:02}:{total % 60:02}"
            )
        job.state, job.message = (
            "completed",
            "Transcript and Codex export ready. Speech timings are estimates."
            if source == "asr"
            else "Transcript and Codex export ready.",
        )

    def _speech(self, job):
        recognized = transcribe_job(job)
        lines = [
            {
                "start": cue["start"],
                "duration": cue["duration"],
                "text": cue["text"],
                "quality_flags": cue["quality_flags"],
            }
            for cue in recognized["segments"]
        ]
        self._complete(job, lines, "asr", "mlx-whisper", recognized["metadata"]["language"], "asr:original")

    def _fail(self, job, exc):
        job.code, job.message = exc.code, str(exc)
        job.state = "cancelled" if exc.code == "cancelled" else "failed"
        # Keep only the current failed job's acquired video/log for a direct
        # speech retry. Starting another job or normal shutdown clears it.
        if job.state == "cancelled" or not job.audio_validated:
            shutil.rmtree(job.directory, ignore_errors=True)

    def cancel(self, identity):
        job = self.get(identity)
        job.cancelled.set()
        job.action.set()
        return job.public()

    def shutdown(self):
        if self.job:
            self.job.cancelled.set()
            self.job.action.set()
        if self.worker:
            self.worker.join(timeout=35)
        if self.job:
            shutil.rmtree(self.job.directory, ignore_errors=True)

    def _wait(self, job, page, timeout=900):
        deadline = time.monotonic() + timeout
        while not job.action.is_set():
            if job.cancelled.is_set() or time.monotonic() >= deadline or page.is_closed():
                raise ExtractionError(
                    "cancelled", "Verification was cancelled or timed out. Start again when ready.", 409
                )
            page.wait_for_timeout(250)
            if job.show_browser.is_set():
                job.show_browser.clear()
                page.bring_to_front()
        job.action.clear()
        if job.cancelled.is_set():
            raise ExtractionError("cancelled", "Extraction cancelled.", 409)

    def _download(self, job, context, url, destination, limit):
        if not safe_media_url(url):
            raise ExtractionError("media_address_rejected", "Douyin returned an unsupported media host.", 422)
        session = requests.Session()
        session.trust_env = False
        for cookie in context.cookies([url]):
            session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])
        try:
            for _ in range(6):
                if not safe_media_url(url):
                    raise ExtractionError("media_address_rejected", "Douyin returned an unsupported media host.", 422)
                with session.get(
                    url, headers={"Referer": job.url}, stream=True, allow_redirects=False, timeout=(15, 30)
                ) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers.get("Location", ""))
                        continue
                    if response.status_code != 200:
                        raise ExtractionError(
                            "media_request_failed",
                            "The media server refused this download. Complete any Douyin verification and retry.",
                            422,
                        )
                    if "text/html" in response.headers.get("Content-Type", ""):
                        raise ExtractionError(
                            "media_request_failed",
                            "Douyin returned a verification page instead of media. Check its browser window.",
                            422,
                        )
                    count = 0
                    with destination.open("wb") as stream:
                        for chunk in response.iter_content(1024 * 1024):
                            if job.cancelled.is_set():
                                raise ExtractionError("cancelled", "Extraction cancelled.", 409)
                            count += len(chunk)
                            if count > limit:
                                raise ExtractionError(
                                    "media_too_large",
                                    "This media exceeds the local download limit. Import a smaller copy instead.",
                                    422,
                                )
                            stream.write(chunk)
                            job.message = f"Downloading the source video… {count // (1024 * 1024)} MB"
                    if count == 0:
                        raise ExtractionError("media_empty", "The media download was empty. Retry the link.", 422)
                    return
            raise ExtractionError(
                "media_redirect_failed", "The media server redirected too many times. Retry the link.", 422
            )
        except requests.RequestException as exc:
            raise ExtractionError(
                "media_connection_failed", "The media connection failed. Check your connection and retry.", 502
            ) from exc
        finally:
            session.close()

    def _run(self, job):
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                profile = Path(
                    os.environ.get(
                        "DOUYIN_BROWSER_PROFILE",
                        str(Path.home() / ".local/share/efficient-content-extractor/douyin-browser"),
                    )
                )
                profile.mkdir(parents=True, exist_ok=True)
                os.chmod(profile, 0o700)
                channel = "chrome" if Path("/Applications/Google Chrome.app").is_dir() else None
                context = playwright.chromium.launch_persistent_context(str(profile), headless=False, channel=channel)
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                    captured = []

                    def observe(response):
                        address = urlsplit(response.url)
                        if address.hostname not in {"www.douyin.com", "douyin.com"} or not address.path.startswith(
                            "/aweme/"
                        ):
                            return
                        try:
                            if (
                                "json" not in response.headers.get("content-type", "")
                                or int(response.headers.get("content-length") or 0) > 8 * 1024 * 1024
                            ):
                                return
                            body = response.body()
                            if len(body) > 8 * 1024 * 1024:
                                return
                            data = json.loads(body)
                            match = find_video(data, job.identity) if job.identity else None
                            if match:
                                captured[:] = [match]
                        except (BrowserError, ValueError, TypeError, KeyError) as exc:
                            LOG.debug("Skipped unreadable playback response (%s)", type(exc).__name__)

                    context.on("response", observe)
                    page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
                    if not job.identity:
                        job.url, job.identity = normalize_url(page.url)
                    job.state, job.message = "reading_video", "Checking this video in your existing Douyin session…"
                    for _ in range(60):
                        if captured:
                            break
                        if job.cancelled.is_set():
                            raise ExtractionError("cancelled", "Extraction cancelled.", 409)
                        page.wait_for_timeout(250)
                        # Public page hydration is a fallback when no detail
                        # response was emitted. Never read account page storage.
                        for script in page.locator('script[id="RENDER_DATA"]').all_text_contents():
                            try:
                                match = find_video(json.loads(unquote(script)), job.identity)
                                if match:
                                    captured[:] = [match]
                            except (ValueError, TypeError):
                                pass
                    if not captured:
                        job.state = "waiting_verification"
                        job.message = "Complete Douyin's requested login or verification, then click Verified — extract transcript."
                        page.bring_to_front()
                        self._wait(job, page)
                        job.state, job.message = (
                            "reading_video",
                            "Verification complete. Acquiring this video automatically…",
                        )
                        page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
                    for _ in range(60):
                        if captured:
                            break
                        if job.cancelled.is_set():
                            raise ExtractionError("cancelled", "Extraction cancelled.", 409)
                        page.wait_for_timeout(250)
                        # Public page hydration is a fallback when no detail
                        # response was emitted. Never read account page storage.
                        for script in page.locator('script[id="RENDER_DATA"]').all_text_contents():
                            try:
                                match = find_video(json.loads(unquote(script)), job.identity)
                                if match:
                                    captured[:] = [match]
                            except (ValueError, TypeError):
                                pass
                    if not captured:
                        raise ExtractionError(
                            "douyin_verification_blocked",
                            "Douyin still did not return this video's playback data. Check its browser page, then retry extraction.",
                            422,
                        )
                    job.video = inspect_video(captured[0])
                    tracks = job.video["tracks"]
                    selected = next(
                        (track for track in tracks if track["id"] == job.choice), tracks[0] if tracks else None
                    )
                    if job.choice and selected and selected["id"] != job.choice:
                        raise ExtractionError(
                            "caption_selection_required",
                            "The selected caption track is no longer available. Retry extraction.",
                            422,
                        )
                    if selected:
                        job.state = "downloading_captions"
                        job.message = "Retrieving the existing caption track…"
                        path = job.directory / "captions.txt"
                        self._download(job, context, selected["_url"], path, 10 * 1024 * 1024)
                        lines = caption_records(path.read_text())
                        source, provider, language = "platform", "douyin-browser", selected["language"]
                        track_id = selected["id"]
                    else:
                        if not job.allow_asr:
                            raise ExtractionError(
                                "captions_not_found",
                                "No caption track was found in the playback data. Enable local speech recognition or import captions.",
                                422,
                            )
                        check_setup()
                        job.state = "downloading_media"
                        job.message = "Downloading the source for local speech recognition…"
                        job.media = job.directory / "source.mp4"
                        last_error = None
                        for address in job.video["_media_urls"][:5]:
                            try:
                                self._download(job, context, address, job.media, 1024 * 1024 * 1024)
                                duration = probe_video(job.media)
                                job.audio_validated = True
                                job.video["duration"] = duration
                                last_error = None
                                break
                            except ExtractionError as exc:
                                if exc.code == "cancelled":
                                    raise
                                last_error = exc
                        if last_error:
                            raise last_error
                        if not job.audio_validated:
                            raise ExtractionError(
                                "media_unavailable",
                                "Douyin returned no usable video with audio. Check playback in its window, then retry extraction.",
                                422,
                            )
                        context.close()
                        self._speech(job)
                    if selected:
                        self._complete(job, lines, source, provider, language, track_id)
                finally:
                    try:
                        context.close()
                    except BrowserError:
                        pass
        except ExtractionError as exc:
            self._fail(job, exc)
        except Exception as exc:  # noqa: BLE001 -- worker boundary: never expose URLs or browser secrets in errors
            LOG.warning("Douyin browser worker failed (%s)", type(exc).__name__)
            self._fail(
                job,
                ExtractionError(
                    "browser_failed",
                    "The Douyin browser could not complete extraction. Check its window and your connection, then retry extraction.",
                    422,
                ),
            )


manager = DouyinManager()
