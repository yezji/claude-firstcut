#!/usr/bin/env bash
# Open an FCPXML in Final Cut Pro (macOS only)
# Usage: bash open_in_fcp.sh /abs/path/rough_cut.fcpxml
#
# .fcpxml is registered to Final Cut, so a single `open` imports it.
# Final Cut launches; the user confirms one import dialog.
set -e
FCPXML="$1"
[ -z "$FCPXML" ] && { echo "Usage: $0 /abs/path/rough_cut.fcpxml"; exit 1; }
[ -f "$FCPXML" ] || { echo "File not found: $FCPXML"; exit 1; }
if [ "$(uname -s)" != "Darwin" ]; then
  echo "Final Cut Pro is macOS-only."; exit 1
fi
open "$FCPXML"
echo "Sent to Final Cut. Confirm the import dialog."
