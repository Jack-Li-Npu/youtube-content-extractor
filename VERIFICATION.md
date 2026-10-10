# Verification

## Chinese speech-caption correction — 2026-10-10

The text-preservation check incorrectly inserted spaces between split caption chunks. This falsely rejected recognized text in languages such as Chinese that do not require spaces between words. The formatter now reconstructs the model's original boundary whitespace for validation, then trims individual displayed cues. It retains the text-preservation check and the original estimated timings.

- **87 backend tests and five multilingual subcases** passed, along with Ruff. New cases cover Chinese, Japanese, Thai, mixed Chinese/English, and English sentence or pause splits, including JSON/SRT/Markdown exports. Non-Chinese cases are synthetic regression coverage, not live recognition accuracy tests.
- Retried the already acquired public Douyin video `7694655284198772011` without another login or download. Offline recognition completed in approximately **65.5 seconds**, producing **605 Chinese segments** from **00:00:00.000 to 00:21:30.300**. All **5,666 non-whitespace recognized characters** were preserved, and the live API and complete Markdown handoff matched the normalized speech output. This checks formatting completeness, not recognition accuracy against the audio.
- The browser displayed **Ready for Codex**, **605 segments**, and the copy/download controls. No server restart was needed because each speech retry launches a new worker from the updated source.

## Douyin release — 2026-10-10

The 2.1 release adds a dedicated browser acquisition flow, manual verification when requested by Douyin, optional offline Apple Silicon speech recognition, resumable speech retries, and local timestamp playback. Detailed setup, a real result screenshot, data retention, and limitations are in [docs/DOUYIN.md](docs/DOUYIN.md).

- **86 backend tests** and **15 frontend tests** passed locally. Coverage includes the existing YouTube behavior, Douyin URL validation, manual confirmation and saved-session paths, sanitized job output, media host restrictions, audio fallback, local range responses, retry/reload behavior, and complete estimated-timing exports.
- Backend Ruff, frontend ESLint, the production build, and Bash syntax checks passed. CI now lints the Douyin services, speech worker, model setup script, and launch scripts as well as the previous YouTube code.
- The earlier live test on **2026-10-08** acquired video `7685972770793999667` through this adapter and produced **466 speech-caption segments**. The completed job was restored after reload; full copy/download payloads matched; a timestamp opened the local player at **402.480 seconds**. No new live extraction or identity verification was performed for the 2026-10-10 publication checks.
- The real-result screenshot is published as a demonstration. Login profiles, credentials, model weights, temporary videos, logs, and complete transcripts are excluded from the release.

The manual verification pause/confirm behavior is covered by synthetic tests. The live run reused a working session, so it did not establish that this app can resolve every real challenge. Broader video and URL coverage remains unverified. Local video rendering and AI screenshot access also depend on the browser/tool environment; later video-brief inspection in the embedded browser failed to complete visual verification. The screenshot demonstrates extraction and handoff, not a successfully illustrated brief.

## Initial GitHub release — 2026-09-29

The release is a clean source snapshot of the local caption-only adaptation. The original application's MIT license is byte-for-byte identical to the license at upstream commit `4928098ffe109df932a8f4bae47f31ebcf314a10`.

Release preparation uses the documented `setup.sh` from an independent checkout, with frozen uv dependencies and `npm ci`. Local checks use Python 3.13.9 and Node.js 25.3.0; GitHub Actions is configured for Python 3.13 and Node.js 22 on Ubuntu.

## Codex handoff update — 2026-10-07

Copy and download now contain the same setup-aware prompt and complete transcript. The prompt requests installation only when `video-brief` is missing, then asks for illustrated takeaways and verified visual timestamps. The full prompt can be expanded on the page.

- **7 frontend tests**, frontend lint, production build, and skill manifest validation passed.
- A clean installation from `Jack-Li-Npu/youtube-content-extractor` (the repository name at that time, now `Jack-Li-Npu/video-content-extractor`) into an isolated test directory matched the bundled skill and its UI metadata byte-for-byte.
- Browser verification with synthetic API responses preserved all **1,104 segments** while search displayed one match; clipboard and downloaded Markdown matched byte-for-byte, including caption timings beyond one hour and instruction-like text inside source fences.
- The download comparison utility confirmed the prompt and complete source content matched the extraction fixture.
- Keyboard expansion of the prompt, the mobile layout at 390 pixels, and the download fallback after denied clipboard access passed; no browser JavaScript errors occurred.

These checks verify the app's handoff and skill-package installation, not end-to-end analysis in a new Codex account. Screenshot inspection still depends on the recipient's tools and source-video access. The prompt explicitly requests a caption-based brief and reported limitations when setup or visual inspection is unavailable.

## Initial release automated checks

- **45 backend tests:** supported URLs, language/source selection, original-language preference, provider fallback, empty/failed results, accurate timing, local origin restrictions, and disabled media downloads.
- **6 frontend tests:** full Markdown text preservation, Unicode and multiline content, millisecond timing beyond an hour, safe source fences, invalid input, repeated/overlapping captions, long transcripts, and safe filenames.
- Frontend lint and production build; backend Ruff; Bash launcher syntax; local API health and static frontend smoke checks.
- CI runs offline tests and the frontend build. Its results appear in the repository's Actions tab; live YouTube access is not required by CI.

## Previous live verification — 2026-09-27

Using the public example video `Hrbq66XqtCo`, the local app retrieved **1,104 uploaded English caption segments**. Browser display, the full clipboard payload, and the generated Markdown were compared against the retrieved source, including every segment in order.

- First cue: `00:00:00.480 → 00:00:04.400`.
- Last cue: `01:43:09.440 → 01:43:10.560`.
- Searching for the final cue left copy/export content complete.
- A selected automatic-English track returned **2,743** segments in a separate live API check.
- A deliberately failed primary provider exercised the real yt-dlp fallback, which returned the same 1,104 uploaded-caption segments.
- The fallback retrieved metadata and caption data, with no audio/video streams, models, or AI-service requests.
- Responsive DOM checks at 1280, 390, and 320 pixels found no horizontal page overflow.

These are historical checks of specific videos and network conditions, not a promise that YouTube access always succeeds. The original multi-format browser downloads were tested in Chrome before the app was simplified. The current single-format handoff was verified through its generated file and complete clipboard content; the embedded Codex browser did not complete Blob downloads. Use Copy for Codex in that browser or a regular browser for downloads.

## Repeat the export comparison

Save the selected `/api/extract` response as JSON and download its Markdown document:

```bash
node scripts/verify-downloads.mjs '/path/to/extract-response.json' '/path/to/download.transcript.md'
```

The script checks exact generated content. Channel and video duration come from `/api/video-info`; include them in the source JSON to validate them independently, otherwise the script takes those two fields from the document being compared.

## Scope

The current release includes YouTube captions and the bounded Douyin workflow described above. TikTok, Bilibili, and a browser extension are not implemented. See [ROADMAP.md](ROADMAP.md). Selected demonstration screenshots are included; complete personal transcripts, local environment settings, login profiles, model files, dependency folders, generated builds, and the original upstream Git history are not included in the published source.
