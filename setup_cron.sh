#!/usr/bin/env bash
# setup_cron.sh — Installs a daily cron job at 7:00 AM local time.
# Run once: bash setup_cron.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3 || command -v python)"
LOG_FILE="$SCRIPT_DIR/digest.log"
CRON_ENTRY="0 7 * * * cd \"$SCRIPT_DIR\" && \"$PYTHON\" main.py >> \"$LOG_FILE\" 2>&1"

echo "Installing cron job:"
echo "  $CRON_ENTRY"
echo ""

# Check if already installed
if crontab -l 2>/dev/null | grep -qF "job-digest/main.py"; then
    echo "⚠️  A job-digest cron entry already exists. Edit it with: crontab -e"
    crontab -l | grep "job-digest"
    exit 0
fi

# Append to existing crontab (or create new)
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
echo "✓ Cron job installed. Digest will run daily at 7:00 AM."
echo "  Logs: $LOG_FILE"
echo ""
echo "To edit or remove: crontab -e"
echo "To test right now: cd \"$SCRIPT_DIR\" && python3 main.py --dry-run"
