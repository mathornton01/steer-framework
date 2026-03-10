#!/bin/bash
# =================================================================================================
# STEER Python test wrapper
# This script is auto-generated during the build process.
# It wraps a Python test so the STEER test scheduler can invoke it as a native executable.
# =================================================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="$SCRIPT_DIR/steer_python_sdk"
TEST_SCRIPT="$SDK_DIR/__TEST_SCRIPT_NAME__"

export PYTHONPATH="$SDK_DIR:$PYTHONPATH"
exec python3 "$TEST_SCRIPT" "$@"
