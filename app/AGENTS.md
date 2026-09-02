## Project Boundary

- These instructions apply throughout `app/`. Repository-root instructions remain authoritative and App-focused tasks start at the repository root.
- The project is `app/dotlineform.xcodeproj`. Its maintained scheme is `dotlineform`, its app target is `dotlineform`, and its Swift Testing target is `dotlineformTests`.
- The app uses one shared Swift 6 target for native Mac and iPad destinations only. Minimum deployment is macOS 26.0 and iPadOS 26.0. Do not add iPhone, Apple Vision, Mac Catalyst, or a second app target without an explicit architecture decision.
- The app bundle identifier is `com.dotlineform.app`; the test bundle identifier is `com.dotlineform.app.tests`.
- App-owned cloud workloads live under `app/services/<service-id>/`. Each service is an independently deployable provider-neutral boundary and is not part of the Xcode target or application bundle.

## Source And Dependencies

- Add only folders and types with a current owner. Keep SwiftUI composition, the WebKit host, bundled resources, service boundaries, and testable domain behavior distinct without pre-creating later Docs Viewer architecture.
- Keep platform-neutral behavior shared. Isolate genuinely platform-specific code at a narrow boundary and prefer compile-time platform checks there over duplicated feature implementations.
- Prefer Apple system frameworks and ordinary Swift. Add a package dependency only when its maintained value exceeds its integration and lifecycle cost.
- Treat bundled HTML, JavaScript, CSS, and other resources as application source. Keep bridge messages typed and narrow; do not spread `WKWebView` mechanics through SwiftUI views.
- Keep Python operation behavior and types independent of Flask, Gunicorn, Google Cloud, and deployment configuration. HTTP adapters translate only the finite JSON contract; they do not own Swift or page state.
- Keep runtime and development dependencies declared inside each service. The root development requirements may include a service's development requirements so the existing Dev Container and Codex setup can support it; do not create a second App-specific Dev Container or setup system.

## Build And Test

- Keep command-line products under `var/app/DerivedData/`. The established unsigned checks are:

```text
xcodebuild -project app/dotlineform.xcodeproj -scheme dotlineform -configuration Debug -destination 'platform=macOS' -derivedDataPath var/app/DerivedData CODE_SIGNING_ALLOWED=NO build
xcodebuild -project app/dotlineform.xcodeproj -scheme dotlineform -configuration Debug -destination 'platform=macOS' -derivedDataPath var/app/DerivedData CODE_SIGNING_ALLOWED=NO test
xcodebuild -project app/dotlineform.xcodeproj -scheme dotlineform -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath var/app/DerivedData CODE_SIGNING_ALLOWED=NO build
xcodebuild -project app/dotlineform.xcodeproj -scheme dotlineform -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath var/app/DerivedData CODE_SIGNING_ALLOWED=NO build-for-testing
```

- Use Xcode for interactive Mac runs and physical-iPad signing, installation, and presentation review. Retain the selected Personal Team identifier in `project.pbxproj` so the project owner's automatic development-signing choice is reproducible; keep Apple-account credentials, certificates and private keys, Xcode-managed provisioning artifacts, and registered-device state local.
- Use Swift Testing for deterministic domain, payload, state, and boundary behavior. Do not add a UI-testing target for ordinary presentation, interaction choreography, typography, focus, or layout; review those manually on the native Mac and physical iPad.
- Choose the smallest check that proves the changed contract. A UI change does not by itself require a permanent automated UI test.
- For `work-on-the-decayed`, create its ignored local environment and run its focused tests from the repository root:

```text
$HOME/miniconda3/bin/python3 -m venv var/app/python/work-on-the-decayed
var/app/python/work-on-the-decayed/bin/python -m pip install --requirement app/services/work-on-the-decayed/requirements-dev.txt
PYTHONPATH=app/services/work-on-the-decayed/src var/app/python/work-on-the-decayed/bin/python -m pytest app/services/work-on-the-decayed/tests
```

- The existing repository Dev Container installs the service development requirements through the root `requirements.txt`. The Cloud Run image instead installs only the service runtime requirements and starts the Gunicorn/Flask adapter declared by the service Dockerfile.
- Treat API enablement, Cloud Build, Artifact Registry creation, first public Cloud Run deployment, and later exposure changes as explicit reviewed operations. Keep the exact current command and resource implications in the service README; do not run it merely to validate local code.

## Project And Tracked State

- Track application source, resources, tests, `project.pbxproj`, required workspace metadata, and any shared scheme needed by command-line use.
- Do not track DerivedData, build products, `xcuserdata`, `.xcuserstate`, signing certificates, private keys, provisioning artifacts, device state, cloud credentials, or local caches.
- Track service source, focused tests, dependency declarations, Dockerfile, `.dockerignore`, `.gcloudignore`, and safe deployment documentation. Do not track virtual environments, downloaded packages, local endpoint overrides, Google Cloud credentials, service-account keys, or copied environment files.
- Prefer Xcode for structural project changes such as adding targets. Simple reviewed build-setting changes may update `project.pbxproj` directly, followed by a plist syntax check and the smallest relevant `xcodebuild` verification.
- Do not commit or push unless the user explicitly requests it.
