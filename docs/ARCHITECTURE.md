# Architecture and extension points

## Current implementation

```text
React interface
  ├─ /api/video-info → yt-dlp metadata and caption choices
  ├─ /api/extract → youtube-transcript-api
  │                  └─ selected-track yt-dlp caption fallback
  ├─ /api/douyin/jobs → dedicated browser + manual verification when needed
  │                     ├─ exposed caption track
  │                     └─ temporary media → optional offline MLX Whisper worker
  └─ complete timestamped Markdown / clipboard
                       ↓ user-controlled handoff
                  external AI assistant + video-brief
                       ↓
                  brief with YouTube links or current-job local Douyin links
```

`backend/app/transcript_service.py` handles YouTube URL parsing, metadata, caption selection, retrieval, normalization, and error classification. `backend/main.py` serves those two API routes, the Douyin job routes and the built React app. The frontend keeps results in memory and generates the handoff document in `frontend/src/lib/transcript.js`.

`backend/app/douyin_service.py` manages one background job, a dedicated headed Playwright profile, manual browser confirmation, matching playback metadata and allowlisted media downloads. Existing caption tracks are preferred; optional speech runs in a separate Python 3.12 worker (`backend/workers/local_subtitles.py`) with locked MLX dependencies in `stt/`. The API process does not import MLX. Current-job media is served locally with range support and fractional hash seeking. Speech orchestration and safe worker diagnostics live in `backend/app/speech_service.py`. The primary button handles manual confirmation or speech retry; other stages continue automatically. Current-job status restores progress/results on browser reload. A failed job with validated audio retains media for direct speech retry; cancellation or replacement/shutdown clears it. Completed media lasts until replacement or normal shutdown. See [DOUYIN.md](DOUYIN.md) for acquisition validation and data handling.

`skills/video-brief/SKILL.md` contains analysis instructions; it is not executed by the web server. It asks the assistant to read all segments, cite source intervals, and flag caption uncertainty. There is no model-service integration in the current app.

## Proposed platform boundary (not yet implemented)

Move platform-specific behavior behind a provider selected from a validated URL. A provider should support metadata inspection, track listing, selected-track retrieval, and timestamp-link generation. Share the normalized segment representation (`start`, `duration`, `text`) and common errors, but retain source-specific identifiers such as a Bilibili part.

YouTube documents retain `youtube-transcript/v1`. Douyin uses `video-transcript/v1` with explicit platform, canonical identity/source URL, caption provenance, estimated/platform timing, review-flag counts and an optional local player URL. Numbered headings remain segment IDs. The analysis skill uses platform-appropriate links; a public Douyin seek parameter is not assumed. Future adapters should preserve this distinction and add video-part identity when required.

## Proposed player boundary (not yet implemented)

The browser extension would contain a platform-specific player bridge responsible for identifying the active video, reading its current playback position, and seeking to a validated timestamp. Keep retrieval independent of the player bridge so a transcript can still be exported without an extension.

A brief import should have a source identity and bounded, finite time intervals. Validate them against the active video before seeking. Account for route changes, multiple videos, and unsupported player states. Seek only in response to a user action; a highlighted takeaway need not automatically start playback.

If the extension uses the local FastAPI service, design a narrow, explicit connection and permissions model. Existing host/origin checks are intentionally limited to the local web app; an extension is not supported by simply adding a wildcard origin. No such bridge or permission mechanism is shipped today.

## Stable behavior to preserve

- YouTube uses existing captions only, with no media/model download or translation.
- Douyin prefers exposed captions; local speech requires explicit enablement and separate setup.
- Keep original caption wording separate from estimated speech text and its review flags.
- Fractional start times and actual durations, including overlap and long videos.
- Explicit extraction errors separate from metadata success.
- Search affects the view; full-document handoff includes every retrieved segment.
- Analysis happens only after the user chooses to send source text to an assistant.

## Independent frontend channels

The interface mounts one `TranscriptWorkspace` per platform and hides the inactive tab without unmounting it. Each instance owns its URL, selected track, transcript, search, errors and pending request state. YouTube requests therefore cannot overwrite a Douyin result, and Douyin polling continues when its tab is hidden. Only the Douyin workspace restores `/api/douyin/current-job`; neither switching tabs nor clearing YouTube sends a Douyin job mutation.

`ChannelTabs` provides labelled tab panels and Arrow Left/Right, Home and End keyboard navigation. Channel mismatches are blocked before submission, while backend URL validation remains authoritative. Token counting starts only when the result's channel is visible and caches the completed estimate for that result. Results are not duplicated into local storage. A reload clears YouTube page state; the current Douyin job can be restored from the running server.
