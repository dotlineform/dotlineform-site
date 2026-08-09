#!/usr/bin/env bash
set -euo pipefail

DERIVED="${DERIVED:-.derived}"
echo "🧹 Removing $DERIVED …"
rm -rf "$DERIVED"
echo "✅ Clean complete."
