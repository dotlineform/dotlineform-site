#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-VideoBlendGUI}"
CONFIGURATION="${CONFIGURATION:-Debug}"
DERIVED="${DERIVED:-.derived}"

APP_PATH="$DERIVED/Build/Products/$CONFIGURATION/${APP_NAME}.app"

if [ ! -d "$APP_PATH" ]; then
  echo "❌ App not found at $APP_PATH. Did the build succeed?"
  exit 1
fi

echo "🚀 Launching $APP_PATH"
open "$APP_PATH"
