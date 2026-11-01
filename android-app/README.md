# TILAKINO Android

Native Android application foundation for TILAKINO.

## Current scope

- Kotlin + Jetpack Compose
- Cinematic dark UI (ink, gold, neon cyan)
- Home, catalog, saved and profile navigation
- Film detail preview screens
- Android min SDK 24
- GitHub Actions debug APK build

> The current build is a UI foundation with sample catalog data. Authentication, real catalog APIs, Telegram/cloud video ingestion, HLS playback, payments and admin services are integration milestones and are not represented as finished features.

## Build locally

Requires JDK 17 and Android SDK 35.

```bash
gradle assembleDebug
```

APK output:

`app/build/outputs/apk/debug/app-debug.apk`

## GitHub Actions

Push to the `android-app` branch or manually run the workflow. The workflow builds and uploads the debug APK as an artifact.
