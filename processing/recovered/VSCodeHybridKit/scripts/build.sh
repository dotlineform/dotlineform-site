#!/usr/bin/env bash
set -euo pipefail

SCHEME="${SCHEME:-VideoBlendGUI}"
PROJECT="${PROJECT:-VideoBlendGUI.xcodeproj}"
CONFIGURATION="${CONFIGURATION:-Debug}"
DERIVED="${DERIVED:-.derived}"
SDK="${SDK:-macosx}"

echo "👉 Building scheme '$SCHEME' in project '$PROJECT' ($CONFIGURATION)"
xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration "$CONFIGURATION" -sdk "$SDK" -derivedDataPath "$DERIVED" build | xcpretty || true

if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "xcpretty not found or failed; running raw xcodebuild…"
  xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration "$CONFIGURATION" -sdk "$SDK" -derivedDataPath "$DERIVED" build
fi

echo "✅ Build done. Products at: $DERIVED/Build/Products/$CONFIGURATION"
