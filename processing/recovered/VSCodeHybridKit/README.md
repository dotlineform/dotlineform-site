# VS Code Hybrid Kit for macOS SwiftUI (Xcode Build/Run)

This kit lets you **edit in VS Code** and **build/run with Xcode** for a macOS app.

## Requirements
- Xcode + Command Line Tools
- macOS app project (e.g., `VideoBlendGUI.xcodeproj`) with a scheme named `VideoBlendGUI`

If your scheme or project name differs, set env vars:
- `SCHEME=YourScheme`
- `PROJECT=YourProject.xcodeproj`
- `APP_NAME=YourAppName`

## Setup
1. Drop `.vscode/` and `scripts/` into your project root.
2. Open the folder in VS Code.
3. Run tasks: **Cmd+Shift+P** → *Tasks: Run Task* → select task.

## Tasks
- **Build (xcodebuild)** → builds app to `.derived/Build/Products/Debug`
- **Run .app** → opens the built app
- **Clean (DerivedData)** → deletes `.derived`
- **Open in Xcode** → opens `.xcodeproj`

## Notes
- Uses local `.derived` for predictable build output location.
- Can be adapted for multiple schemes/targets by duplicating tasks.
