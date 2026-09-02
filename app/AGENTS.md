## Project Boundary

- These instructions apply throughout `app/`. Repository-root instructions remain authoritative and App-focused tasks start at the repository root.
- The project is `app/dotlineform.xcodeproj`. Its maintained scheme is `dotlineform`, its app target is `dotlineform`, and its Swift Testing target is `dotlineformTests`.
- The app uses one shared Swift 6 target for native Mac and iPad destinations only. Minimum deployment is macOS 26.0 and iPadOS 26.0. Do not add iPhone, Apple Vision, Mac Catalyst, or a second app target without an explicit architecture decision.
- The app bundle identifier is `com.dotlineform.app`; the test bundle identifier is `com.dotlineform.app.tests`.

## Source And Dependencies

- Add only folders and types with a current owner. Keep SwiftUI composition, the WebKit host, bundled resources, service boundaries, and testable domain behavior distinct without pre-creating later Docs Viewer architecture.
- Keep platform-neutral behavior shared. Isolate genuinely platform-specific code at a narrow boundary and prefer compile-time platform checks there over duplicated feature implementations.
- Prefer Apple system frameworks and ordinary Swift. Add a package dependency only when its maintained value exceeds its integration and lifecycle cost.
- Treat bundled HTML, JavaScript, CSS, and other resources as application source. Keep bridge messages typed and narrow; do not spread `WKWebView` mechanics through SwiftUI views.

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

## Project And Tracked State

- Track application source, resources, tests, `project.pbxproj`, required workspace metadata, and any shared scheme needed by command-line use.
- Do not track DerivedData, build products, `xcuserdata`, `.xcuserstate`, signing certificates, private keys, provisioning artifacts, device state, cloud credentials, or local caches.
- Prefer Xcode for structural project changes such as adding targets. Simple reviewed build-setting changes may update `project.pbxproj` directly, followed by a plist syntax check and the smallest relevant `xcodebuild` verification.
- Do not commit or push unless the user explicitly requests it.
