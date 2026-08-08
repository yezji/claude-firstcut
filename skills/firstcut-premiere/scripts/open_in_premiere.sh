#!/usr/bin/env bash
# Launch Premiere and automate XML import (macOS / Windows)
#
# Usage: bash open_in_premiere.sh /abs/path/rough_cut.xml
#
# macOS  : launch -> wait for window -> Cmd+I (Import)
#          -> Cmd+Shift+G (path field) -> type XML path -> Open
#          First run requires Accessibility permission for the terminal
#          (System Settings -> Privacy & Security -> Accessibility).
# Windows: launch only, then print the Ctrl+I instruction (SendKeys focus
#          is unreliable; prefer the MCP route when available).
#
# Failure is harmless: one manual Ctrl/Cmd+I imports the XML, and absolute
# paths mean media links automatically.
set -e
XML_PATH="$1"
[ -z "$XML_PATH" ] && { echo "Usage: $0 /abs/path/rough_cut.xml"; exit 1; }
[ -f "$XML_PATH" ] || { echo "File not found: $XML_PATH"; exit 1; }

case "$(uname -s)" in
  Darwin)
    APP=$(ls -d /Applications/Adobe\ Premiere\ Pro*/Adobe\ Premiere\ Pro*.app 2>/dev/null | sort | tail -1)
    [ -z "$APP" ] && { echo "Premiere Pro installation not found."; exit 1; }
    echo "Launching: $APP"
    open -a "$APP"
    osascript <<EOF
set xmlPath to "$XML_PATH"
tell application "System Events"
  -- wait for Premiere to load (home screen or project window)
  repeat 60 times
    if exists (process "Adobe Premiere Pro") then exit repeat
    delay 1
  end repeat
  tell process "Adobe Premiere Pro"
    set frontmost to true
    delay 8
    -- Import only works with an open project; if stuck at the home screen,
    -- the user must open a project first.
    keystroke "i" using {command down}
    delay 2
    -- type the path directly in the file dialog (Cmd+Shift+G)
    keystroke "g" using {command down, shift down}
    delay 1
    keystroke xmlPath
    delay 0.5
    key code 36 -- return (go to path)
    delay 1
    key code 36 -- return (open)
  end tell
end tell
EOF
    echo "Import keystrokes sent. Check the sequence in Premiere."
    echo "(If no dialog appeared: open a project, then rerun.)"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    PREMIERE=$(ls "/c/Program Files/Adobe/"Adobe\ Premiere\ Pro*/Adobe\ Premiere\ Pro.exe 2>/dev/null | sort | tail -1)
    [ -z "$PREMIERE" ] && { echo "Premiere Pro installation not found."; exit 1; }
    "$PREMIERE" &
    echo "Premiere launched."
    echo "Open a project, then import via Ctrl+I: $XML_PATH"
    echo "(Media links automatically - no relink needed.)"
    ;;
  *)
    echo "Unsupported OS. Import manually in Premiere: $XML_PATH"
    ;;
esac
