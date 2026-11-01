# TILAKINO Android

Native Android application foundation for TILAKINO.

## Current scope

- Kotlin + Jetpack Compose
- Cinematic dark UI (ink, gold, neon cyan)
- Home, catalog, saved and profile navigation
- Film detail preview screens
- Android min SDK 24
- Firebase Android configuration and Authentication SDK dependencies
- GitHub Actions debug APK build and signing fingerprint report

> The current build is a UI foundation with sample catalog data. Firebase phone and Google providers are enabled in the console, but sign-in screens and flows still need to be implemented and tested. Real catalog APIs, Telegram/cloud video ingestion, HLS playback, payments and admin services remain integration milestones.

## Build locally

Requires JDK 17 and Android SDK 35.

```bash
gradle :app:signingReport
gradle assembleDebug
```

APK output:

`app/build/outputs/apk/debug/app-debug.apk`

## GitHub Actions

Push to the `android-app` branch or manually run the workflow. The workflow prints Android signing fingerprints (SHA-1/SHA-256) in the build log and uploads the debug APK as an artifact.
