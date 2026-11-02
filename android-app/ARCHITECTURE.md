# TILAKINO Android architecture

The Android client follows a feature-first MVVM structure as the project grows.

## Planned package boundaries

- `core/designsystem`: colors, typography, reusable cinematic components
- `core/network`: API client, auth interceptors, error mapping
- `core/session`: token storage and signed-in state
- `data/model`: API and persistence DTOs
- `data/repository`: repository implementations
- `domain/model`: app-facing models
- `domain/repository`: repository contracts
- `feature/home`: home feed and featured collections
- `feature/catalog`: movie, series, anime and animation discovery
- `feature/details`: title details, cast, seasons and episodes
- `feature/player`: Media3 playback, HLS, subtitles and resume position
- `feature/profile`: profile, language and account
- `feature/premium`: subscription and payment state

## Security boundaries

- Never embed API secrets, payment secrets or storage credentials in the APK.
- Authentication tokens must be stored using Android secure storage.
- Playback URLs should be short-lived and issued after server-side entitlement checks.
- Telegram file identifiers and cloud object keys are backend data, not public catalog URLs.
- Premium status must be validated by the backend, not trusted from local UI state.

## Current implementation

The first milestone intentionally keeps the UI in one activity file to make the initial build small and easy to verify. The package boundaries above are the target for subsequent refactoring as real backend and playback features are added.
