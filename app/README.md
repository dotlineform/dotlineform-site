# Dotlineform App

This retained SwiftUI application is the native Mac and iPad foundation for Dotlineform. It uses one shared Swift 6 target, a narrow WebKit host, and an App-owned Cloud Run service boundary. It does not support iPhone.

## Requirements

- Xcode 26.6 with the macOS and iOS 26.5 SDKs.
- macOS 26 or later for the native Mac app.
- A connected iPad running iPadOS 26 or later for physical-device review.
- A locally configured Apple development team for signed Mac and iPad runs.

The free Personal Team is the retained development boundary. App Store distribution, TestFlight, archives, and notarization are not planned; consider a paid Apple Developer Program membership only if the current seven-day device provisioning and reinstall cadence becomes a material nuisance.

## Open And Run

Open `app/dotlineform.xcodeproj` and use the maintained `dotlineform` scheme. Select **My Mac** for native Mac review or the connected iPad for signing, installation, and physical-device review.

Signing credentials, device registration, trust, and provisioning remain in Xcode and the Apple account; they are not repository inputs.

## Repeatable Check

From the repository root:

```text
bin/app-check
```

This runs the focused Swift tests on Mac and builds the app and test bundle for a generic iPad device without signing. Products remain under ignored `var/app/DerivedData/`.

Routine checks intentionally remain Debug builds. SAF-1.6 review will run one unsigned Release build for native Mac and generic iPad to verify the optimized configurations, without adding Release compilation to every `bin/app-check` run or starting a distribution workflow.

On a Mac with local development signing configured, also verify the signed application and its sandbox capabilities:

```text
bin/app-check --signed-mac
```

In Codex, every command that invokes `xcodebuild`, including this wrapper, must start with escalated sandbox permission because Xcode's preview macro plugin cannot run its nested sandbox inside the Codex workspace sandbox.

## Configuration And Cloud Service

`dotlineform/App/AppConfiguration.swift` owns the single non-secret development endpoint bundled into the application. A second environment is the trigger to replace that literal with an Xcode configuration boundary; do not introduce environment machinery before then.

The provider-neutral Python workload, local commands, Cloud Run deployment gate, and current resource identifiers are documented in `services/work-on-the-decayed/README.md`. Cloud deployment is separate from the application check and always requires explicit review.

## Development Rules

Read `app/AGENTS.md` before App work. It owns the exact project boundary, source conventions, dependency policy, focused verification, tracked-state rules, and cloud-operation approval boundary.

Repository `.codex/config.toml` is intentionally ignored and machine-local because trust, approval, and external writable-root settings belong to each host. A new development Mac must configure the repository as a trusted project with equivalent permissions and its own valid external Docs Viewer root; do not copy another machine's absolute paths into tracked configuration.
