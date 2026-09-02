#!/usr/bin/env bash
# Runtime smoke test executed on a CI emulator.
#
# This lives in a file rather than inline in the workflow because
# reactivecircus/android-emulator-runner runs each line of its `script:`
# input as a SEPARATE `sh -c` invocation. Shell variables do not survive
# between lines and multi-line constructs (if/fi, loops) are split across
# shells and fail with "Syntax error: end of file unexpected". The
# workflow invokes this as a single line so the whole thing runs in one
# shell.
#
# Purpose: a green build says nothing about whether the app runs. The app
# has been dying on the presplash with no Android-level crash event (a
# clean Python-side exit is not a Java crash/ANR), so Firebase Test Lab
# reported "no crashes" while the app never started. This captures the
# Python traceback in CI instead.
set -u

APK=$(ls bin/*.apk 2>/dev/null | head -1)
echo "APK: ${APK:-<none>}"
if [ -z "$APK" ]; then
  echo "FAIL: no APK in bin/ — nothing to test"
  exit 1
fi

adb install -r "$APK"

echo "=== INSTALLED THIRD-PARTY PACKAGES ==="
adb shell pm list packages -3 | tr -d '\r'

PKG=$(adb shell pm list packages -3 | tr -d '\r' | sed 's/^package://' | grep -iE 'wtracker|kivy' | head -1)
echo "RESOLVED PACKAGE: ${PKG:-<none found>}"
if [ -z "$PKG" ]; then
  echo "FAIL: APK installed but no matching package — see the full list above"
  exit 1
fi

echo "RESOLVED LAUNCH ACTIVITY:"
adb shell cmd package resolve-activity --brief "$PKG" | tr -d '\r' | tail -1

adb logcat -c
# monkey with the LAUNCHER category starts whatever entry activity the
# manifest declares, so no hardcoded class name (a previous attempt
# guessed org.kivy.android.PythonActivity and launched nothing).
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1
# Give Python time to boot, import, and fail.
sleep 45

echo "===================== PYTHON LOG ====================="
# p4a tags Python output (tracebacks included) as "python".
adb logcat -d -s python:V | tr -d '\r' || true

echo "================== BROAD PATTERN GREP ==============="
# Fallback in case output is not tagged "python".
adb logcat -d 2>/dev/null | tr -d '\r' \
  | grep -iE "traceback|modulenotfound|importerror|no module|python|kivy|wtracker|AndroidRuntime|FATAL" \
  | tail -150 || true

echo "===================== PROCESS STATE ================="
if adb shell ps -A | tr -d '\r' | grep -i "$PKG"; then
  echo "PROCESS IS RUNNING (app survived startup)"
else
  echo "PROCESS NOT RUNNING (died during startup)"
fi
echo "====================================================="
