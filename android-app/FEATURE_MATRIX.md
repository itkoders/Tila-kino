# TILAKINO Android + Telegram Feature Delivery Matrix

This is the acceptance checklist for bringing the Telegram product and the 30 agreed product ideas into the Android app. A checkbox is only marked complete after implementation, automated checks where practical, and device/server verification. UI-only placeholders do not count.

## Shared platform foundation
- [ ] One shared PostgreSQL source of truth for Telegram and Android.
- [ ] Firebase ID-token verification on the server; secure account linking and session expiry.
- [ ] Server-side admin RBAC; primary Telegram admin ID 6359925487; Android admin identity linked to a verified Firebase UID (never email-only client checks).
- [ ] API authorization, input validation, rate limiting, audit logs, safe error handling.
- [ ] DB migrations, backups, restore test, pagination, indexes, observability and health checks.

## Telegram parity
- [ ] Movies, series, seasons, episodes; poster, metadata and unique 4-digit codes.
- [ ] Search by title, code, episode, genre, actor; typo-tolerant search.
- [ ] Uzbek, Russian, English, Tajik locale and per-title audio availability.
- [ ] Favorites (Premium-only if that policy remains enabled), watch history and resume position.
- [ ] Premium plans: 1 month 10,000 UZS; 2 months 20,000 UZS; 6 months 40,000 UZS; 1 year 60,000 UZS.
- [ ] Premium expiry downgrade; reminders 3 days before and on expiry day.
- [ ] Promo codes, gift/trial Premium, referral links and referral rewards.
- [ ] Payment proof/manual review plus real provider integrations after merchant credentials are supplied.
- [ ] Ordinary-tier sponsor messages and Premium ad-free entitlement.
- [ ] Required-channel subscription checks configurable by admin.
- [ ] User profile, block/unblock, support/report issue, broadcast and notification preferences.
- [ ] Admin catalog CRUD, episode CRUD, payment review, plans, sponsors, required channels, users, stats, broadcasts and helper-admin permission scopes.
- [ ] Telegram video delivery and cloud playback; only authorized content.

## Android features — 30 agreed ideas
1. [ ] Personalized recommendations.
2. [ ] Typo-tolerant smart search.
3. [ ] Actor search.
4. [ ] Resume playback from saved position.
5. [ ] Watch-later list.
6. [ ] 1–10 title ratings.
7. [ ] User reviews with moderation/reporting.
8. [ ] Trending and top-rated charts.
9. [ ] Premiere calendar.
10. [ ] New-title alerts by preferred genres.
11. [ ] Subtitle selection.
12. [ ] Audio/dubbing language selection.
13. [ ] Adaptive quality selection.
14. [ ] Data-saver mode.
15. [ ] Mini-player / picture-in-picture where supported.
16. [ ] Playback screen-on behavior and safe system controls.
17. [ ] Sleep timer.
18. [ ] Trailer playback.
19. [ ] Stills/gallery.
20. [ ] Cast, director and title metadata.
21. [ ] Profile watch-time and viewing statistics.
22. [ ] Admin-configurable Premium trial campaign.
23. [ ] Gift Premium to another account.
24. [ ] Promo-code generator with expiry/use limits.
25. [ ] Secure QR device sign-in/linking.
26. [ ] Active device/session management and remote sign-out.
27. [ ] Kids mode and age-rating filter.
28. [ ] Privacy controls and watch-history management.
29. [ ] Broken-video/content report workflow.
30. [ ] Admin live operations dashboard for server, playback, payments and errors.

## Visual design and accessibility
- [ ] Cinematic black/gold visual identity, polished mobile layouts and responsive states.
- [ ] Animated hero banners and inner-screen backdrops with reduced-motion option.
- [ ] Accessible contrast, scalable text, touch targets, loading/empty/error/offline states.
- [ ] Consistent navigation, player controls, cards, filters and profile/subscription screens.

## Release gates
- [ ] Unit and API integration tests; DB migration and authorization tests.
- [ ] Android build succeeds and APK installs on supported Redmi/Xiaomi Android devices.
- [ ] Real Firebase email, Google and phone sign-in tested with configured SHA fingerprints and SMS region.
- [ ] Telegram and Android account data parity verified using the same test account.
- [ ] Playback, subtitles, resume, quality, entitlement and network failure tested.
- [ ] Payment sandbox/live callback signature, duplicate callback and amount mismatch tested.
- [ ] Admin/helper-admin permission matrix and audit trail tested.
- [ ] Backup/restore, rate limits, crash-free smoke test and production health check completed.

## Current verified baseline (2026-11-02)
- [x] Android Gradle workflow compiled successfully at commit f69c14eea205bfa0fb1838d504165933ee554b91 (GitHub Actions run 41406491550).
- [ ] This successful compile is not proof that the listed product features are implemented or that the app has passed real-device acceptance.
- [ ] Current Android screen still contains sample film data/local favorites; it is not yet connected to the production backend.
- [ ] Existing backend documents Telegram webhook/catalog/admin functionality, but real Click/Payme/Uzum integrations are not implemented; a signed generic callback and manual proof workflow are not a substitute for a merchant integration.
