# Verification

## Channel separation and interface refinement — 2026-10-11

YouTube and Douyin now have explicit, keyboard-accessible tabs and independently mounted workspaces. A running Douyin job keeps polling while YouTube is selected; switching tabs does not start, confirm, cancel or replace it. Each channel retains its own link, selected caption track, transcript, search, errors and pending requests in page memory. Reload starts on YouTube, and the Douyin tab restores its current server job.

- **88 backend tests, five multilingual subcases, and 20 frontend tests passed**, along with Ruff, ESLint, the production build and shell syntax checks. New unit coverage includes wrong-channel links across supported URL shapes and the background status labels. Dependencies and lockfiles are unchanged.
- Browser checks against an isolated deterministic local fixture covered: YouTube metadata without a recommended language, selected Chinese automatic captions, a YouTube response arriving while Douyin was active, manual-verification pause, show-window action, confirmation, background completion, speech retry, cancellation, and restoration after reload. Arrow Left/Right, Home and End changed both selection and keyboard focus. Drafts, language and search survived switching. No real account challenge was completed for these UI checks.
- With a search matching only the last of two fixture captions, YouTube copy/download remained byte-identical and contained both captions and the fractional `01:01:01.250` start. A wrong-channel link disabled submission before a request. Fixture request logs confirmed platform-specific API routes; speech retry did not submit another acquisition job.
- The real, already completed 237-segment Douyin job was restored into the new interface without another browser login, media download or model run. Its complete browser copy matched the API-derived handoff byte-for-byte (**23,722 UTF-8 bytes**) while search displayed one cue. The screenshots in README show the actual local interface, not fixture output.
- The actual app was visually checked at **1280 px** and **390 px** widths; the mobile page's scroll width was 390 px, with no horizontal overflow. Dark tokens were also inspected in an isolated preview using the production CSS values. All primary text/button/helper token pairs passed WCAG AA contrast; the lowest checked ratio was **4.61:1**. Reduced motion disables transitions, and no automatic decorative animations are used.
- Lighthouse 12.8.2 on the production build at the real local server: **Performance 91, Accessibility 100, Best Practices 100, SEO 100**. Simulated mobile metrics were FCP **2.6 s**, LCP **3.0 s**, CLS **0.015**, TBT **0 ms**. Dark-token preview accessibility scored **100**. These are local lab results, not field Core Web Vitals or an INP measurement; simulated LCP remains above the 2.5-second target. Tokenizer loading is deferred for inactive channels, and completed estimates are retained when switching back.

Design audit: preserve the existing Geist/Geist Mono typography, caption mark, rust accent, local-first workflow and MIT attribution. Apply design-taste-frontend's relevant refinement guidance with variance **5**, motion **3**, density **3**. Retire the shared ambiguous URL form, decorative section numbers, floating hero explainer, fake paper illustration, and tiny helper text. Use one semantic light/dark token system and consistent radii. Marketing-only image walls, motion showcases, pricing blocks and hero conversion requirements do not apply to this extraction tool. Original video titles and caption wording remain source data, including their punctuation.

This release changes interface organization, not platform permissions or speech accuracy. The live YouTube bot-check limitation in the system check below is unchanged. Manual-verification browser states here are fixture coverage, not new evidence that a real Douyin identity check succeeds.

## System check — 2026-10-11

The Chinese text-preservation correction below was rechecked, followed by fresh acquisitions of two additional public Douyin videos and live requests for four YouTube videos. The local YouTube proxy setting was empty at first, producing `connection_failed`. Restoring the existing `http://127.0.0.1:7890` proxy established connectivity, but YouTube then returned bot checks. No authentication bypass or cookie import was attempted.

| Source and input format | Live result | Caption range / checks |
| --- | --- | --- |
| [Douyin electric phenomena](https://www.douyin.com/video/7687991485467966031), `/video/…` | Fresh acquisition; 65 Chinese ASR segments from a 178.833-second video | `00:00:00.000–00:02:57.960`; local inference including audio decoding took 11.823 seconds |
| [Douyin hairy-ball theorem](https://www.douyin.com/video/7631965839184432424), `jingxuan?modal_id=…` | Fresh acquisition; 237 Chinese ASR segments from a 445.405-second video | `00:00:00.000–00:07:24.120`; local inference including audio decoding took 24.868 seconds |
| [YouTube Hrbq66XqtCo](https://www.youtube.com/watch?v=Hrbq66XqtCo), watch URL | `502 request_blocked` during metadata inspection | No new captions retrieved |
| [YouTube aircAruvnKk](https://www.youtube.com/watch?v=aircAruvnKk), `youtu.be` URL | `502 request_blocked` during metadata inspection | No new captions retrieved |
| [YouTube iG9CE55wbtY](https://www.youtube.com/watch?v=iG9CE55wbtY), embed URL | `502 request_blocked` during metadata inspection | No new captions retrieved |
| [YouTube 5DMutq7W__w](https://www.youtube.com/watch?v=5DMutq7W__w), watch URL | `502 request_blocked` during metadata inspection | No new captions retrieved |

For both new Douyin results, the live API matched every normalized cue's text, timing and review flags. All non-whitespace recognized characters were preserved from the native ASR output. The complete browser clipboard and downloaded Markdown matched the generated handoff byte-for-byte. Filtering the 237-segment result to one match did not truncate its handoff. These are completeness checks, not speech-recognition accuracy measurements; the recognized text contains errors and important words still need playback review.

Local playback decoded visible frames at **36.280 and 95.800 seconds** in the first video and **152.300 and 300.500 seconds** in the second (`readyState=4`, no media error). Actual playback advanced in the first sample. HTTP range retrieval returned `206` with the requested bytes. The result survived a page reload. A malformed Douyin hostname returned `400 invalid_url` without replacing the completed job; a foreign POST origin returned `403`. The YouTube browser flow showed the blocked-request error and no false transcript success. Neither new Douyin test requested manual verification; a working saved session was reused, so real identity/CAPTCHA handling remains unverified.

The check found and corrected an additional download bug: the long Chinese title generated a **315-byte filename** and did not save. Filename shortening now budgets UTF-8 bytes without splitting Unicode characters; the same browser download saved successfully with a **197-byte filename**, preserving the video ID and complete transcript. A regression covers long Chinese, emoji and ASCII titles. The misleading whitespace-based word count was removed, and clipboard failures now give a clear download fallback.

- **88 backend tests, five multilingual subcases, and 16 frontend tests passed.** Coverage includes selected uploaded/automatic tracks, caption-only fallback, empty/failed results, millisecond exports beyond one hour, source fencing, manual-confirmation/retry states, and speech opt-out preventing media downloads and model setup.
- Backend Ruff, frontend ESLint, the production build, Bash syntax checks, and both offline uv lockfile checks passed. No dependencies changed.
- YouTube remains caption-only, with media downloads disabled. Speech inference uses the already installed local model in offline mode; this check downloaded no model weights and made no cloud AI requests. Browser acquisition/media requests are necessary for the two Douyin ASR tests.
- Selected UI/player screenshots are published in [the Douyin guide](docs/DOUYIN.md#additional-video-checks--2026-10-11). Full transcripts, media, worker logs, local proxy settings and browser profiles remain outside Git.

Current limits: successful new YouTube extraction could not be established under the tested network conditions; new live Douyin tests exercised ASR, not an exposed platform-caption track. Those track-selection and fallback paths have offline coverage. This sample does not establish universal platform access, caption accuracy, or successful illustrated analysis by Codex.

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

Save the selected `/api/extract` response as JSON and download its Markdown document. For Douyin, save the completed `/api/douyin/jobs/{id}` response or `/api/douyin/current-job`; the utility reads its nested result:

```bash
node scripts/verify-downloads.mjs '/path/to/extract-response.json' '/path/to/download.transcript.md'
```

The script checks exact generated content. Channel and video duration come from `/api/video-info`; include them in the source JSON to validate them independently, otherwise the script takes those two fields from the document being compared.

## Scope

The current release includes YouTube captions and the bounded Douyin workflow described above. TikTok, Bilibili, and a browser extension are not implemented. See [ROADMAP.md](ROADMAP.md). Selected demonstration screenshots are included; complete personal transcripts, local environment settings, login profiles, model files, dependency folders, generated builds, and the original upstream Git history are not included in the published source.
