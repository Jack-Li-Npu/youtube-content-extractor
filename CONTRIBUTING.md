# Contributing

Start with the [README](README.md), [roadmap](ROADMAP.md), and [architecture notes](docs/ARCHITECTURE.md). The current release supports YouTube captions and an experimental Douyin browser workflow with optional local speech recognition, verified on one public video. Please do not advertise broader Douyin coverage, planned providers, or extension features as implemented.

For a new platform, propose the supported URL types, accessible caption source, timing fidelity, error cases, and timestamp navigation behavior. Keep platform parsing/retrieval separate from the shared UI and export logic. A browser-player adapter should be independently testable from caption retrieval.

Use small, synthetic or redistributable fixtures. Verify selection of the intended caption track, complete text preservation, timing beyond one hour, missing/empty captions, and provider failures. A seek feature should verify source identity and interval bounds. Do not commit cookies, tokens, local `.env` files, personal transcripts, generated builds, or dependency environments.

Run the checks in the README before submitting a pull request. Keep upstream attribution and third-party notices intact. Describe the user-visible behavior and relevant validation, including any platform limitations. Keep Douyin speech recognition optional, local, and clearly labelled as estimated. Cloud AI-service calls, additional transcription backends, persistent libraries, and public hosting need an explicit product decision; they are not implicit parts of adding another caption provider. Test browser workflows with synthetic responses in CI; never commit a real login profile or automate identity verification.
